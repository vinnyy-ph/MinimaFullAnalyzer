from backend.CodegenTAC.code_generator import TACGenerator
from backend.Lexer.minima_lexer import Lexer
from backend.Semantic.semantic_analyzer import SemanticAnalyzer
from backend.Syntax.syntax_analyzer import analyze_syntax
from backend.CodegenTAC.interpreter import TACInterpreter
import uuid
import time
import sys
import traceback
from io import StringIO
execution_states = {}
def format_minima_number(value):
    """
    Format a number for output according to Minima language rules.
    - Use hyphen (-) for negative numbers
    - Limit decimal places to maximum of 9 digits without rounding
    - Ensure integers are within -999999999 to 999999999
    """
    if not isinstance(value, (int, float)):
        return value
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, int):
        if value < 0:
            return f"-{abs(value)}"
        return str(value)
    
    # For floating point values, use direct string representation to avoid rounding errors
    # This is especially important for large values with many decimal places
    str_val = f"{value}"
    
    # If the string contains scientific notation, convert it to a regular decimal format
    if 'e' in str_val.lower():
        from decimal import Decimal, getcontext
        getcontext().prec = 100
        decimal_val = Decimal(str_val)
        str_val = f"{decimal_val:.30f}".rstrip('0').rstrip('.')
    
    # Determine sign and split parts
    sign = "-" if value < 0 else ""
    abs_str = str_val.lstrip('-')
    
    if '.' in abs_str:
        int_part, frac_part = abs_str.split('.')
        
        # Limit decimal places to 9 without rounding
        if len(frac_part) > 9:
            frac_part = frac_part[:9]
        
        # Remove trailing zeros
        frac_part = frac_part.rstrip('0')
        
        # Assemble result - only include decimal point if we have a fractional part
        if frac_part:
            return f"{sign}{int_part}.{frac_part}"
        else:
            return f"{sign}{int_part}"
    else:
        # It's actually an integer stored as a float
        return f"{sign}{abs_str}"
def format_minima_output(output_text):
    """
    Ensure all negative numbers in output are displayed with hyphen notation.
    This provides a second layer of formatting in case the interpreter missed anything.
    Also trims any decimal places to max 9 digits.
    """
    import re
    def replace_negatives(match):
        number = match.group(1)
        if '.' in number:  
            parts = number.split('.')
            if len(parts) > 1 and len(parts[1]) > 9:
                parts[1] = parts[1][:9]
            return f"-{parts[0]}.{parts[1]}" if len(parts) > 1 else f"-{parts[0]}"
        else:  
            return f"-{number}"
    formatted_text = re.sub(r'(?<!\w)-(\d+(?:\.\d+)?)', replace_negatives, output_text)
    formatted_text = re.sub(r'(^|\s+)-(\d+(?:\.\d+)?)', lambda m: m.group(1) + "-" + m.group(2), formatted_text)
    formatted_text = re.sub(r'([\[\(,])-(\d+(?:\.\d+)?)', lambda m: m.group(1) + "-" + m.group(2), formatted_text)
    def trim_decimals(match):
        whole = match.group(1)
        decimal = match.group(2)
        if len(decimal) > 9:
            # Truncate without rounding to preserve original digits
            decimal = decimal[:9]
        return f"{whole}.{decimal}"
    # First handle the case of 10+ decimal places
    formatted_text = re.sub(r'((?:-)?\d+)\.(\d{10,})', trim_decimals, formatted_text)
    # Also catch any cases that might have been rounded during string conversion
    formatted_text = re.sub(r'((?:-)?\d+\.\d*?)9{3,}(\d*)', lambda m: f"{m.group(1)}{m.group(2)}", formatted_text)
    return formatted_text
def execute_code(code, execution_id=None, user_input=None, debug_mode=False):
    """
    Execute Minima code and return the results.
    Args:
        code (str): The Minima code to execute
        execution_id (str, optional): Execution ID if resuming with input
        user_input (str, optional): User input if resuming execution
        debug_mode (bool, optional): Enable debug output
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
    
    # Apply debug mode if requested
    if debug_mode:
        results['terminalOutput'] += "Running in debug mode\n"
    
    interpreter = None
    if execution_id and execution_id in execution_states:
        interpreter, state = execution_states.pop(execution_id)
        try:
            if user_input is not None:
                user_input = str(user_input)
            output_segment = interpreter.resume_with_input(user_input)
            results['success'] = True
            results['output'] = output_segment
            results['tac'] = interpreter.instructions
            results['formattedTAC'] = format_tac_instructions(interpreter.instructions, interpreter.source_positions)
            results['terminalOutput'] = f"Execution resumed with input: {user_input}\n"
            results['terminalOutput'] += f"Steps executed: {interpreter.steps_executed}\n"
        except Exception as e:
            results['error'] = f"Execution Error: {str(e)}"
            results['terminalOutput'] = f"Error when processing input: {str(e)}\n"
            results['terminalOutput'] += traceback.format_exc()
            results['success'] = False
        if interpreter and interpreter.waiting_for_input:
            new_execution_id = str(uuid.uuid4())
            execution_states[new_execution_id] = (interpreter, 'input_wait')
            results['waitingForInput'] = True
            results['inputPrompt'] = interpreter.input_prompt
            results['executionId'] = new_execution_id
            results['terminalOutput'] += f"\nWaiting for input with prompt: {interpreter.input_prompt}"
            if results['success']:
                results['success'] = True
        elif interpreter:
            results['waitingForInput'] = False
            results['terminalOutput'] += f"\nExecution completed after {interpreter.steps_executed} total steps.\n"
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
        code_generator = TACGenerator(debug_mode=debug_mode)
        tac_instructions = code_generator.generate(parse_tree)
        source_positions = getattr(code_generator, 'source_positions', None)
        
        results['tac'] = tac_instructions
        results['formattedTAC'] = format_tac_instructions(tac_instructions, source_positions)
        results['terminalOutput'] += f"Generated {len(tac_instructions)} TAC instructions.\n"
        
        interpreter = TACInterpreter().load(tac_instructions, source_positions)
        interpreter.debug_mode = debug_mode
        max_steps = float('inf')
        interpreter.max_execution_steps = max_steps
        start_time = time.time()
        output_segment = interpreter.run()
        end_time = time.time()
        execution_time = end_time - start_time
        results['output'] = output_segment
        if interpreter.steps_executed >= max_steps:
            results['error'] = f"Execution exceeded maximum of {max_steps} steps. Potential infinite loop detected."
            results['terminalOutput'] += f"\n----- Execution Log -----\n"
            results['terminalOutput'] += f"Code executed in {execution_time:.3f} seconds.\n"
            results['terminalOutput'] += f"Execution terminated after {max_steps} steps to prevent infinite loop.\n"
            results['success'] = False
        else:
            results['success'] = True
            results['terminalOutput'] += f"\n----- Execution Log -----\n"
            results['terminalOutput'] += f"Code executed in {execution_time:.3f} seconds.\n"
    except Exception as e:
        results['error'] = f"Execution Error: {str(e)}"
        results['terminalOutput'] += f"\nError during initial execution: {str(e)}\n"
        results['terminalOutput'] += traceback.format_exc()
        results['success'] = False
    if interpreter and interpreter.waiting_for_input:
        execution_id = str(uuid.uuid4())
        execution_states[execution_id] = (interpreter, 'input_wait')
        results['waitingForInput'] = True
        results['inputPrompt'] = interpreter.input_prompt
        results['executionId'] = execution_id
        if results['success']:
            results['success'] = True
        results['terminalOutput'] += f"Waiting for input with prompt: {interpreter.input_prompt}\n"
    elif interpreter and results['success']:
        results['waitingForInput'] = False
        results['terminalOutput'] += f"Execution completed after {interpreter.steps_executed} total steps.\n"
    if 'output' in results and results['output']:
        results['output'] = format_minima_output(results['output'])    
    return results
def format_tac_instructions(tac_instructions, source_positions=None):
    """
    Format TAC instructions for display.
    
    Args:
        tac_instructions: List of TAC instructions
        source_positions: Optional list of source positions (line, column) for each instruction
    
    Returns:
        Formatted string representation of TAC instructions
    """
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
        
        # Add source position if available
        if source_positions and i < len(source_positions) and source_positions[i]:
            line, col = source_positions[i]
            instr_str += f" (line {line}, col {col})"
            
        formatted_lines.append(instr_str)
    return '\n'.join(formatted_lines)