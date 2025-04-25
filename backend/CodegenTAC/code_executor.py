from backend.Lexer.minima_lexer import Lexer
from backend.Syntax.syntax_analyzer import analyze_syntax
from backend.CodegenTAC.interpreter import TACInterpreter
from backend.semantic_codegen_visitor import SemanticAndCodeGenVisitor
import uuid
import time
import sys
import traceback
execution_states = {}
def execute_code(code, execution_id=None, user_input=None):
    """
    Execute Minima code using the integrated semantic/codegen visitor.
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
            output = interpreter.resume_with_input(user_input)
            results['success'] = True
            results['output'] = output
            results['tac'] = getattr(interpreter, 'instructions', [])
            results['formattedTAC'] = format_tac_instructions(results['tac'])
            results['terminalOutput'] = f"Execution resumed with input: {user_input}\n"
            results['terminalOutput'] += f"Steps executed so far: {getattr(interpreter, 'steps_executed', 'N/A')}\n"
            if interpreter.waiting_for_input:
                new_execution_id = str(uuid.uuid4())
                execution_states[new_execution_id] = (interpreter, 'input_wait')
                results['waitingForInput'] = True
                results['inputPrompt'] = interpreter.input_prompt
                results['executionId'] = new_execution_id
                results['terminalOutput'] += f"Waiting again for input: {interpreter.input_prompt}\n"
            else:
                 results['terminalOutput'] += "Execution completed.\n"
        except Exception as e:
            results['error'] = f"Execution Error: {str(e)}"
            results['terminalOutput'] = f"Error resuming execution: {str(e)}\n{traceback.format_exc()}"
            results['success'] = False 
        return results
    try:
        lexer = Lexer(code)
        tokens = [] 
        while True:
            token = lexer.get_next_token()
            if token is None: break
            tokens.append(token)
        if lexer.errors:
            lex_errors_str = ', '.join([f"L{e.line}:C{e.column} - {e.message}" for e in lexer.errors])
            results['error'] = f'Lexical Errors: {lex_errors_str}'
            results['terminalOutput'] = results['error']
            return results
        syntax_success, parse_tree_or_error = analyze_syntax(code)
        if not syntax_success:
            syntax_error_details = parse_tree_or_error 
            error_msg = syntax_error_details.get('message', 'Unknown syntax error')
            line = syntax_error_details.get('line', '?')
            column = syntax_error_details.get('column', '?')
            results['error'] = f"Syntax Error: L{line}:C{column} - {error_msg}"
            results['terminalOutput'] = results['error']
            return results
        parse_tree = parse_tree_or_error
        compiler_visitor = SemanticAndCodeGenVisitor()
        semantic_errors_list, tac_instructions = compiler_visitor.analyze_and_generate(parse_tree)
        if semantic_errors_list:
            sem_errors_str = ', '.join([f"L{e.line}:C{e.column} - {e.message}" for e in semantic_errors_list])
            results['error'] = f'Semantic Errors: {sem_errors_str}'
            results['terminalOutput'] = results['error']
            results['tac'] = tac_instructions
            results['formattedTAC'] = format_tac_instructions(tac_instructions)
            return results
        results['tac'] = tac_instructions
        results['formattedTAC'] = format_tac_instructions(tac_instructions)
        results['terminalOutput'] += f"Semantic checks passed.\nGenerated {len(tac_instructions)} TAC instructions.\n"
        interpreter = TACInterpreter()
        interpreter.instructions = tac_instructions
        interpreter.load(tac_instructions)
        max_steps = float('inf') 
        interpreter.set_execution_limit(max_steps)
        try:
            start_time = time.time()
            output = interpreter.run() 
            end_time = time.time()
            execution_time = end_time - start_time
            current_limit = interpreter.max_execution_steps
            if current_limit is not None and interpreter.steps_executed >= current_limit:
                 results['error'] = f"Execution exceeded maximum steps ({current_limit}). Potential infinite loop."
                 results['terminalOutput'] += f"\n----- Execution Log -----\n"
                 results['terminalOutput'] += f"Code executed in {execution_time:.4f} seconds.\n"
                 results['terminalOutput'] += f"Execution terminated after {interpreter.steps_executed} steps.\n"
                 results['success'] = False 
            else:
                results['success'] = True
                results['output'] = output
                results['terminalOutput'] += f"\n----- Execution Log -----\n"
                results['terminalOutput'] += f"Code executed in {execution_time:.4f} seconds.\n"
                results['terminalOutput'] += f"Execution completed in {interpreter.steps_executed} steps.\n"
        except Exception as exec_err:
            results['error'] = f"Runtime Error: {str(exec_err)}"
            results['terminalOutput'] += f"\nRuntime Error: {str(exec_err)}\n{traceback.format_exc()}"
            results['success'] = False
        if interpreter.waiting_for_input:
            execution_id = str(uuid.uuid4())
            execution_states[execution_id] = (interpreter, 'input_wait')
            results['waitingForInput'] = True
            results['inputPrompt'] = interpreter.input_prompt
            results['executionId'] = execution_id
            results['success'] = True
            results['terminalOutput'] += f"Execution paused, waiting for input: {interpreter.input_prompt}\n"
    except Exception as compile_err:
        results['error'] = f"Compilation Error: {str(compile_err)}"
        results['terminalOutput'] += f"Error during compilation phase: {str(compile_err)}\n{traceback.format_exc()}"
        results['success'] = False
    return results
def format_tac_instructions(tac_instructions):
    """Format TAC instructions for display."""
    if not tac_instructions:
        return ""
    formatted_lines = []
    line_num_width = len(str(len(tac_instructions) - 1)) if tac_instructions else 1
    for i, instruction_tuple in enumerate(tac_instructions):
        if isinstance(instruction_tuple, (list, tuple)) and len(instruction_tuple) == 4:
            op, arg1, arg2, result = instruction_tuple
        else:
            formatted_lines.append(f"{i:>{line_num_width}}: MALFORMED INSTRUCTION: {instruction_tuple}")
            continue
        def format_operand(operand, is_label_target=False, is_prompt=False):
            if operand is None:
                return ""
            if isinstance(operand, str):
                if is_prompt or (operand.startswith('"') and operand.endswith('"')) or (operand.startswith("'") and operand.endswith("'")):
                     return f"'{operand}'" 
                elif not is_label_target and not operand.startswith('t_') and not operand.startswith('L_') and not operand.isalnum():
                     return str(operand)
                else:
                    return str(operand) 
            return str(operand) 
        s_arg1 = format_operand(arg1, is_prompt=(op == 'INPUT'))
        s_arg2 = format_operand(arg2)
        s_result = format_operand(result, is_label_target=(op in ['GOTO', 'IFTRUE', 'IFFALSE', 'LABEL']))
        line_str = f"{i:>{line_num_width}}: "
        if op == 'LABEL':
            line_str += f"{s_result}:"
        elif op == 'FUNCTION_BEGIN':
             params = ', '.join(map(str, arg2)) if isinstance(arg2, list) else ''
             line_str += f"FUNCTION {arg1} ({params}) BEGIN [{result} locals]" 
        elif op == 'FUNCTION_END':
             line_str += f"FUNCTION {arg1} END"
        elif op == 'GOTO':
            line_str += f"GOTO {s_result}"
        elif op in ['IFTRUE', 'IFFALSE']:
            line_str += f"{op} {s_arg1} GOTO {s_result}"
        elif op == 'PRINT':
            line_str += f"PRINT {s_arg1}"
        elif op == 'INPUT':
            line_str += f"{s_result} = INPUT {s_arg1}" 
        elif op == 'RETURN':
            line_str += f"RETURN {s_arg1}" if arg1 is not None else "RETURN"
        elif op == 'PARAM':
             line_str += f"PARAM {s_arg1}" 
        elif op == 'CALL':
             call_str = f"CALL {s_arg1}, {s_arg2}"
             if result is not None:
                 line_str += f"{s_result} = {call_str}"
             else:
                 line_str += call_str
        elif op == 'ASSIGN':
            line_str += f"{s_result} = {s_arg1}"
        elif op in ['ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'LT', 'LE', 'GT', 'GE', 'EQ', 'NEQ', 'AND', 'OR', 'CONCAT', 'LIST_CONCAT']:
            line_str += f"{s_result} = {s_arg1} {op} {s_arg2}"
        elif op in ['NEG', 'NOT']:
            line_str += f"{s_result} = {op} {s_arg1}"
        elif op == 'TYPECAST':
             line_str += f"{s_result} = ({s_arg2}) {s_arg1}"
        elif op == 'LIST_CREATE':
             line_str += f"{s_result} = []"
        elif op == 'LIST_APPEND':
             line_str += f"APPEND {s_arg1}, {s_arg2}"
        elif op == 'LIST_ACCESS':
             line_str += f"{s_result} = {s_arg1}[{s_arg2}]"
        elif op == 'LIST_SET':
             line_str += f"{s_arg1}[{s_arg2}] = {s_result}"
        elif op == 'DICT_CREATE':
             line_str += f"{s_result} = {{}}"
        elif op == 'DICT_SET':
             line_str += f"{s_arg1}{{{s_arg2}}} = {s_result}" 
        elif op == 'DICT_ACCESS':
             line_str += f"{s_result} = {s_arg1}{{{s_arg2}}}"
        else:
            parts = [str(p) for p in [op, arg1, arg2, result] if p is not None]
            line_str += " ".join(parts)
        formatted_lines.append(line_str)
    return '\n'.join(formatted_lines)