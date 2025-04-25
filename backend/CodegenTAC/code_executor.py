from backend.CodegenTAC.code_generator import TACGenerator
from backend.Lexer.minima_lexer import Lexer
from backend.Semantic.semantic_analyzer import SemanticAnalyzer
from backend.Syntax.syntax_analyzer import analyze_syntax
from backend.CodegenTAC.interpreter import TACInterpreter
import uuid
import time
import sys
import traceback
execution_states = {}
def format_minima_number(value):
    """
    Format a number for output according to Minima language rules.
    - Use tilde (~) for negative numbers
    - Limit decimal places to maximum of 9 digits
    - Ensure integers are within ~999999999 to 999999999
    """
    if not isinstance(value, (int, float)):
        return value
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if value < 0:
        if isinstance(value, float):
            formatted = f"~{abs(value):.9f}".rstrip('0').rstrip('.')
            parts = formatted.split('.')
            if len(parts) > 1 and len(parts[1]) > 9:
                parts[1] = parts[1][:9]
                formatted = f"~{parts[0]}.{parts[1]}"
            return formatted
        else:
            return f"~{abs(value)}"
    else:
        if isinstance(value, float):
            formatted = f"{value:.9f}".rstrip('0').rstrip('.')
            parts = formatted.split('.')
            if len(parts) > 1 and len(parts[1]) > 9:
                parts[1] = parts[1][:9]
                formatted = f"{parts[0]}.{parts[1]}"
            return formatted
        else:
            return str(value)
def format_minima_output(output_text):
    """
    Ensure all negative numbers in output are displayed with tilde notation.
    This provides a second layer of formatting in case the interpreter missed anything.
    Also trims any decimal places to max 9 digits.
    """
    import re
    
    # First handle negative numbers with tilde
    def replace_negatives(match):
        number = match.group(1)
        if '.' in number:  
            parts = number.split('.')
            if len(parts) > 1 and len(parts[1]) > 9:
                parts[1] = parts[1][:9]
            return f"~{parts[0]}.{parts[1]}" if len(parts) > 1 else f"~{parts[0]}"
        else:  
            return f"~{number}"
    
    # Apply tilde notation for negative numbers
    formatted_text = re.sub(r'-(\d+(\.\d+)?)', replace_negatives, output_text)
    
    # Now trim all decimal places to max 9 digits
    def trim_decimals(match):
        whole = match.group(1)
        decimal = match.group(2)
        if len(decimal) > 9:
            decimal = decimal[:9]
        return f"{whole}.{decimal}"
    
    # Apply decimal place trimming for all numbers with more than 9 decimal places
    formatted_text = re.sub(r'((?:~)?\d+)\.(\d{10,})', trim_decimals, formatted_text)
    
    return formatted_text
def execute_code(code, execution_id=None, user_input=None):
    """
    Execute Minima code and return the results.
    Args:
        code (str): The Minima code to execute
        execution_id (str, optional): Execution ID if resuming with input
        user_input (str, optional): User input if resuming execution
    Returns:
        dict: A dictionary containing execution results and metadata
    """
    results = {
        'success': False,
        'output': '',
        'tac': [],
        'formattedTAC': '',
        'error': '',
        'waitingForInput': False,
        'inputPrompt': '',
        'executionId': None,
        'terminalOutput': ''
    }
    if execution_id and execution_id in execution_states:
        interpreter, state = execution_states.pop(execution_id)
        try:
            # Ensure user_input is always a string - remove any automatic conversion
            if user_input is not None:
                user_input = str(user_input)
            output = interpreter.resume_with_input(user_input)
            results['success'] = True
            results['output'] = format_minima_output(output)  
            results['tac'] = interpreter.instructions
            results['formattedTAC'] = format_tac_instructions(interpreter.instructions)
            results['terminalOutput'] = f"Execution resumed with input: {user_input}\n"
            results['terminalOutput'] += f"Steps executed: {interpreter.steps_executed}\n"
        except Exception as e:
            results['error'] = f"Execution Error: {str(e)}"
            results['terminalOutput'] = f"Error when processing input: {str(e)}\n"
            results['terminalOutput'] += traceback.format_exc()
        if interpreter.waiting_for_input:
            new_execution_id = str(uuid.uuid4())
            execution_states[new_execution_id] = (interpreter, 'input_wait')
            results['waitingForInput'] = True
            results['inputPrompt'] = interpreter.input_prompt
            results['executionId'] = new_execution_id
            results['terminalOutput'] += f"\nWaiting for input with prompt: {interpreter.input_prompt}"
        return results
    try:
        lexer = Lexer(code)
        tokens = []
        while True:
            token = lexer.get_next_token()
            if token is None:
                break
            tokens.append(token)
        if lexer.errors:
            results['error'] = 'Lexical Errors: ' + ', '.join(error.message for error in lexer.errors)
            return results
        success, parse_tree_or_error = analyze_syntax(code)
        if not success:
            results['error'] = 'Syntax Error: ' + parse_tree_or_error['message']
            return results
        parse_tree = parse_tree_or_error
        semantic_analyzer = SemanticAnalyzer()
        semantic_errors = semantic_analyzer.analyze(parse_tree)
        if semantic_errors:
            results['error'] = 'Semantic Errors: ' + ', '.join(error.message for error in semantic_errors)
            return results
        code_generator = TACGenerator()
        tac_instructions = code_generator.generate(parse_tree)
        results['tac'] = tac_instructions
        results['formattedTAC'] = format_tac_instructions(tac_instructions)
        results['terminalOutput'] += f"Generated {len(tac_instructions)} TAC instructions.\n"
        interpreter = TACInterpreter().load(tac_instructions)
        max_steps = float('inf')
        interpreter.max_execution_steps = max_steps
        try:
            start_time = time.time()
            output = interpreter.run()
            end_time = time.time()
            execution_time = end_time - start_time
            if interpreter.steps_executed >= max_steps:
                results['error'] = f"Execution exceeded maximum of {max_steps} steps. Potential infinite loop detected."
                results['terminalOutput'] += f"\n----- Execution Log -----\n"
                results['terminalOutput'] += f"Code executed in {execution_time:.3f} seconds.\n"
                results['terminalOutput'] += f"Execution terminated after {max_steps} steps to prevent infinite loop.\n"
                results['success'] = False
            else:
                results['success'] = True
                results['output'] = output
                results['terminalOutput'] += f"\n----- Execution Log -----\n"
                results['terminalOutput'] += f"Code executed in {execution_time:.3f} seconds.\n"
                results['terminalOutput'] += f"Execution completed after {interpreter.steps_executed} steps.\n"
        except Exception as e:
            results['error'] = f"Execution Error: {str(e)}"
            results['terminalOutput'] += f"\nError during execution: {str(e)}\n"
            results['terminalOutput'] += traceback.format_exc()
        if interpreter.waiting_for_input:
            execution_id = str(uuid.uuid4())
            execution_states[execution_id] = (interpreter, 'input_wait')
            results['waitingForInput'] = True
            results['inputPrompt'] = interpreter.input_prompt
            results['executionId'] = execution_id
            results['success'] = True
            results['terminalOutput'] += f"Waiting for input with prompt: {interpreter.input_prompt}\n"
    except Exception as e:
        results['error'] = f"Execution Error: {str(e)}"
        results['terminalOutput'] += f"Error during compilation: {str(e)}\n"
        results['terminalOutput'] += traceback.format_exc()
    if 'output' in results and results['output']:
        results['output'] = format_minima_output(results['output'])    
    return results
def format_tac_instructions(tac_instructions):
    """Format TAC instructions for display."""
    formatted_lines = []
    for i, (op, arg1, arg2, result) in enumerate(tac_instructions):
        parts = []
        if op == 'INPUT':
            parts.append(f"'{arg1}'")  
        elif arg1 is not None:
            parts.append(str(arg1))
        if arg2 is not None:
            parts.append(str(arg2))
        if result is not None:
            parts.append(str(result))
        instr_str = f"{i}: {op} {', '.join(parts)}"
        formatted_lines.append(instr_str)
    return '\n'.join(formatted_lines)