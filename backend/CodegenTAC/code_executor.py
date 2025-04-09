from backend.CodegenTAC.code_generator import TACGenerator
from backend.Lexer.minima_lexer import Lexer
from backend.Semantic.semantic_analyzer import SemanticAnalyzer
from backend.Syntax.syntax_analyzer import analyze_syntax
from backend.CodegenTAC.interpreter import TACInterpreter

def execute_code(code):
    """
    Execute Minima code and return the results.
    
    Returns:
        dict: A dictionary containing:
            - 'success': True/False
            - 'output': The runtime output
            - 'tac': The generated TAC instructions
            - 'error': Error message if success is False
    """
    results = {
        'success': False,
        'output': '',
        'tac': [],
        'error': ''
    }
    
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
        
        # Execute the TAC instructions
        interpreter = TACInterpreter().load(tac_instructions)
        output = interpreter.run()
        
        results['success'] = True
        results['output'] = output
        
    except Exception as e:
        results['error'] = f"Execution Error: {str(e)}"
    
    return results

def format_tac_instructions(tac_instructions):
    """Format TAC instructions for display."""
    formatted_lines = []
    for i, (op, arg1, arg2, result) in enumerate(tac_instructions):
        parts = []
        if arg1 is not None:
            parts.append(str(arg1))
        if arg2 is not None:
            parts.append(str(arg2))
        if result is not None:
            parts.append(str(result))
        instr_str = f"{i}: {op} {', '.join(parts)}"
        formatted_lines.append(instr_str)
    return '\n'.join(formatted_lines)
