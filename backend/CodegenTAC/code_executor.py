from backend.CodegenTAC.code_generator import TACGenerator
from backend.Lexer.minima_lexer import Lexer
from backend.Semantic.semantic_analyzer import SemanticAnalyzer
from backend.Syntax.syntax_analyzer import analyze_syntax
from backend.CodegenTAC.interpreter import TACInterpreter
import uuid
import time
import sys
import traceback

# Store execution states
execution_states = {}

def format_minima_output(output_text):
    """
    Ensure all negative numbers in output are displayed with tilde notation.
    This provides a second layer of formatting in case the interpreter missed anything.
    """
    import re
    
    # Replace minus signs with tildes in numeric output
    # Careful not to replace minus signs in other contexts
    # This regex looks for minus signs followed by digits
    formatted_text = re.sub(r'-(\d+(\.\d+)?)', r'~\1', output_text)
    
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
    
    # If this is resuming an existing execution with input
    if execution_id and execution_id in execution_states:
        interpreter, state = execution_states.pop(execution_id)
        
        try:
            # Convert tilde negative notation if needed in user input
            if isinstance(user_input, str) and user_input.startswith('~'):
                # No need to convert here, the interpreter will handle it
                pass
            
            # Provide the user input and resume execution
            output = interpreter.resume_with_input(user_input)
            results['success'] = True
            results['output'] = format_minima_output(output)  # Apply formatting
            results['tac'] = interpreter.instructions
            results['formattedTAC'] = format_tac_instructions(interpreter.instructions)
            
            # Track terminal output
            results['terminalOutput'] = f"Execution resumed with input: {user_input}\n"
            results['terminalOutput'] += f"Steps executed: {interpreter.steps_executed}\n"
            
        except Exception as e:
            results['error'] = f"Execution Error: {str(e)}"
            results['terminalOutput'] = f"Error when processing input: {str(e)}\n"
            results['terminalOutput'] += traceback.format_exc()
        
        # Check if we're waiting for more input
        if interpreter.waiting_for_input:
            new_execution_id = str(uuid.uuid4())
            execution_states[new_execution_id] = (interpreter, 'input_wait')
            results['waitingForInput'] = True
            results['inputPrompt'] = interpreter.input_prompt
            results['executionId'] = new_execution_id
            results['terminalOutput'] += f"\nWaiting for input with prompt: {interpreter.input_prompt}"
        
        return results
    try:
        # Lexical Analysis
        lexer = Lexer(code)
        tokens = []
        while True:
            token = lexer.get_next_token()
            if token is None:
                break
            tokens.append(token)
        
        if lexer.errors:
            # Lexical errors found
            results['error'] = 'Lexical Errors: ' + ', '.join(error.message for error in lexer.errors)
            return results
        
        # Syntax Analysis
        success, parse_tree_or_error = analyze_syntax(code)
        if not success:
            # Syntax errors found
            results['error'] = 'Syntax Error: ' + parse_tree_or_error['message']
            return results
        
        parse_tree = parse_tree_or_error
        
        # Semantic Analysis
        semantic_analyzer = SemanticAnalyzer()
        semantic_errors = semantic_analyzer.analyze(parse_tree)
        if semantic_errors:
            # Found semantic errors
            results['error'] = 'Semantic Errors: ' + ', '.join(error.message for error in semantic_errors)
            return results
        
        # Code Generation
        code_generator = TACGenerator()
        tac_instructions = code_generator.generate(parse_tree)
        results['tac'] = tac_instructions
        results['formattedTAC'] = format_tac_instructions(tac_instructions)
        
        # Add debug info about instructions
        results['terminalOutput'] += f"Generated {len(tac_instructions)} TAC instructions.\n"
        
        # Execute the TAC instructions with a timeout and step limit
        interpreter = TACInterpreter().load(tac_instructions)
        
        # Configure execution limits and debug mode
        max_steps = float('inf')
        interpreter.max_execution_steps = max_steps
        
        # Optional: Enable debug mode for troubleshooting 
        # interpreter.debug_mode = True
        
        try:
            # Track execution time
            start_time = time.time()
            
            # Run the interpreter
            output = interpreter.run()
            
            # Calculate execution time
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Check if execution was terminated due to step limit
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
        
        # Check if execution is waiting for input
        if interpreter.waiting_for_input:
            # Generate a unique ID for this execution
            execution_id = str(uuid.uuid4())
            # Store the interpreter state
            execution_states[execution_id] = (interpreter, 'input_wait')
            # Update results to indicate waiting for input
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
            parts.append(f"'{arg1}'")  # Format prompt as a string
        elif arg1 is not None:
            parts.append(str(arg1))
        if arg2 is not None:
            parts.append(str(arg2))
        if result is not None:
            parts.append(str(result))
        instr_str = f"{i}: {op} {', '.join(parts)}"
        formatted_lines.append(instr_str)
    return '\n'.join(formatted_lines)