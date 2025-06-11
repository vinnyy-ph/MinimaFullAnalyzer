import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.Lexer.minima_lexer import Lexer  
from backend.Syntax.syntax_analyzer import analyze_syntax, parser
from backend.Semantic.semantic_analyzer import SemanticAnalyzer 
from backend.CodegenTAC.code_executor import execute_code, format_tac_instructions
from backend.CodegenTAC.built_in_functions import MinimaBultins
import io
from contextlib import redirect_stdout
app = Flask(__name__)
CORS(app)
execution_states = {} #debugging purposes
@app.route('/analyze_full', methods=['POST'])
def analyze_full():
    data = request.get_json()
    minima_code_input = data.get('code', '')
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        lexer = Lexer(minima_code_input)
        all_tokens = lexer.tokenize_all()
        tokens = []
        for token in all_tokens:
            token_info = {
                'type': token.type, # could be IDENTIFIER, INTEGERLITERAL, etc.
                'value': token.value, # the actual value of the token, examples are x, 123, etc.
                'line': token.line, # the line number where the token was found
                'column': token.column # the column number where the token was found
            }
            if token.warning:
                token_info['warning'] = token.warning
            tokens.append(token_info)
        
        # Split warnings from errors
        lexical_errors = []
        lexical_warnings = []
        for issue in lexer.errors:
            if hasattr(issue, 'is_warning') and issue.is_warning:
                lexical_warnings.append(issue.to_dict())
            else:
                lexical_errors.append(issue.to_dict())
        
        syntax_errors = []
        semantic_errors  = []
        if not lexical_errors: #if lexical_errors dictionary is empty, continue with syntax analysis
            # Pass the tokens and lexical errors to avoid redundant analysis
            success, result = analyze_syntax(minima_code_input, pre_analyzed_tokens=all_tokens, lexical_errors=lexical_errors)
            if success:
                parse_tree = result
                semantic_analyzer = SemanticAnalyzer()
                semantic_analyzer.analyze(parse_tree)
                semantic_errors = [error.to_dict() for error in semantic_analyzer.errors]
            else:
                syntax_errors = [result]
                semantic_errors = [{
                    "type": "semantic",
                    "message": "Syntax errors detected. Resolve them before semantic analysis."
                }]
        else:
            syntax_errors = [{
                "type": "syntax",
                "message": "Lexical errors detected. Resolve them before syntax analysis."
            }]
            semantic_errors = [{
                "type": "semantic",
                "message": "Lexical errors detected. Resolve them before syntax and semantic analysis."
            }]
    terminal_output = output_buffer.getvalue()
    return jsonify({
        'tokens': tokens,
        'lexicalErrors': lexical_errors,
        'lexicalWarnings': lexical_warnings,
        'syntaxErrors': syntax_errors,
        'semanticErrors': semantic_errors,
        'terminalOutput': terminal_output
    })
@app.route('/getSymbolTable', methods=['POST'])
def get_symbol_table():
    data = request.get_json()
    minima_code_input = data.get('code', '')
    
    if not minima_code_input:
        return jsonify({
            'success': False,
            'error': 'No code provided'
        })
    
    try:
        # First check for lexical errors
        lexer = Lexer(minima_code_input)
        all_tokens = lexer.tokenize_all()
        
        # Filter out warnings from actual errors
        lexical_errors = [error for error in lexer.errors if not (hasattr(error, 'is_warning') and error.is_warning)]
        
        if lexical_errors:
            return jsonify({
                'success': False,
                'error': 'Lexical errors detected. Cannot generate symbol table.'
            })
        
        # If no lexical errors, try to parse
        success, result = analyze_syntax(minima_code_input, pre_analyzed_tokens=all_tokens, lexical_errors=lexical_errors)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Syntax errors detected. Cannot generate symbol table.',
                'syntaxError': result
            })
        
        # Run semantic analysis to build the symbol table
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.analyze(result)
        
        if semantic_analyzer.errors:
            # If there are semantic errors, we still return the symbol table but flag the issues
            has_errors = True
        else:
            has_errors = False
        
        # Convert the symbol table to a JSON-friendly format
        symbols = []
        
        # Dictionary to track which functions variables belong to
        function_scopes = {}
        
        # First, collect function definitions to initialize function_scopes
        for name, symbol in semantic_analyzer.global_scope.functions.items():
            return_type = "empty"
            if name in semantic_analyzer.function_returns:
                return_info = semantic_analyzer.function_returns[name]
                if isinstance(return_info, tuple) and len(return_info) >= 1:
                    return_type = return_info[0]
            
            symbols.append({
                'name': name,
                'kind': 'function',
                'scope': 'global',
                'params': symbol.params,
                'returnType': return_type,
                'line': symbol.line,
                'column': symbol.column
            })
            
            # Initialize scope tracking for this function
            function_scopes[name] = []
        
        # Helper function to recursively process all scopes
        def process_symbol_table(scope, parent_scope_name=None):
            # Process variables in this scope
            for name, symbol in scope.variables.items():
                var_type = "unknown"
                var_value = None
                
                if hasattr(symbol, "value") and symbol.value:
                    if isinstance(symbol.value, tuple) and len(symbol.value) >= 1:
                        var_type = symbol.value[0]
                        if len(symbol.value) >= 2:
                            var_value = str(symbol.value[1]) if symbol.value[1] is not None else "null"
                
                # Determine the scope type
                scope_type = "global"
                if parent_scope_name:
                    scope_type = f"local:{parent_scope_name}"
                
                symbol_info = {
                    'name': name,
                    'kind': 'variable',
                    'scope': scope_type,
                    'type': var_type,
                    'value': var_value,
                    'fixed': symbol.fixed,
                    'line': symbol.line,
                    'column': symbol.column
                }
                
                symbols.append(symbol_info)
                
                # If this is a function parameter, track it
                if parent_scope_name and name in semantic_analyzer.global_scope.functions.get(parent_scope_name, {}).params:
                    symbol_info['isParameter'] = True
                
                # Track local variables for each function
                if parent_scope_name and parent_scope_name in function_scopes:
                    function_scopes[parent_scope_name].append(symbol_info)
        
        # Process all global variables
        process_symbol_table(semantic_analyzer.global_scope)
        
        # Process function scopes
        for function_name, function_locals in semantic_analyzer.function_scopes.items():
            if function_locals:
                # We need to store the parameter values separately since they are stored in the scope
                for local_scope in function_locals:
                    process_symbol_table(local_scope, function_name)
        
        # Add built-in functions
        builtin_functions = semantic_analyzer.builtin_functions
        for name, info in builtin_functions.items():
            symbols.append({
                'name': name,
                'kind': 'function',
                'scope': 'builtin',
                'params': info.get('params', -1),  # -1 means variable arguments
                'returnType': info.get('return_type', 'unknown'),
                'isBuiltin': True
            })
        
        return jsonify({
            'success': True,
            'symbols': symbols,
            'hasErrors': has_errors
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error generating symbol table: {str(e)}'
        })
@app.route('/getAST', methods=['POST'])
def get_ast():
    data = request.get_json()
    minima_code_input = data.get('code', '')
    
    if not minima_code_input:
        return jsonify({
            'success': False,
            'error': 'No code provided'
        })
    
    try:
        # First check for lexical errors
        lexer = Lexer(minima_code_input)
        all_tokens = lexer.tokenize_all()
        
        # Filter out warnings from actual errors
        lexical_errors = [error for error in lexer.errors if not (hasattr(error, 'is_warning') and error.is_warning)]
        
        if lexical_errors:
            return jsonify({
                'success': False,
                'error': 'Lexical errors detected. Cannot generate AST.'
            })
        
        # If no lexical errors, try to parse
        success, result = analyze_syntax(minima_code_input, pre_analyzed_tokens=all_tokens, lexical_errors=lexical_errors)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Syntax errors detected. Cannot generate AST.',
                'syntaxError': result
            })
        
        # Convert the parse tree to a JSON-friendly format
        def process_tree(node):
            if hasattr(node, 'data') and hasattr(node, 'children'):
                return {
                    'name': str(node.data),
                    'children': [process_tree(child) for child in node.children]
                }
            elif hasattr(node, 'value') and hasattr(node, 'type'):
                return {
                    'name': f"{node.type}: {node.value}"
                }
            else:
                return {'name': str(node)}
        
        ast_json = process_tree(result)
        
        return jsonify({
            'success': True,
            'ast': ast_json
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating AST: {str(e)}'
        })
@app.route('/executeCode', methods=['POST'])
def execute_code_route():
    data = request.json
    minima_code_input = data.get('code', '')
    execution_id = data.get('executionId')
    user_input = data.get('userInput')
    if execution_id:
        print(f"Continuing execution {execution_id} with input: {user_input}")
    else:
        print(f"New code execution request of length {len(minima_code_input)}")
    result = execute_code(minima_code_input, execution_id, user_input)
    if result is None:
        return jsonify({
            'success': False,
            'error': 'Execution failed - no result returned',
            'terminalOutput': 'Internal error: code execution returned None'
        })
    if result.get('tac'):  
        result['formattedTAC'] = format_tac_instructions(result['tac'])
    return jsonify(result)
@app.route('/api/builtin-functions', methods=['GET'])
def get_builtin_functions():
    """Return the list of built-in function names for the editor highlighting"""
    builtin_functions = list(MinimaBultins.BUILTIN_FUNCTIONS.keys())
    return jsonify(builtin_functions)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)