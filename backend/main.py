from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.Lexer.minima_lexer import Lexer  
from backend.Syntax.syntax_analyzer import analyze_syntax, parser
from backend.Semantic.semantic_analyzer import SemanticAnalyzer 
from backend.CodegenTAC.code_executor import execute_code, format_tac_instructions
import io
import sys
import uuid
from contextlib import redirect_stdout
from backend.CodegenTAC.built_in_functions import MinimaBultins
app = Flask(__name__)
CORS(app)
execution_states = {}
@app.route('/analyzeFull', methods=['POST'])
def analyze_full():
    data = request.get_json()
    code = data.get('code', '')
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        lexer = Lexer(code)
        tokens = []
        while True:
            token = lexer.get_next_token()
            if token is None:
                break
            tokens.append({
                'type': token.type,
                'value': token.value,
                'line': token.line,
                'column': token.column
            })
        lexical_errors = [error.to_dict() for error in lexer.errors]
        syntax_errors = []
        semantic_errors = []
        if not lexical_errors:
            success, result = analyze_syntax(code)
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
        'syntaxErrors': syntax_errors,
        'semanticErrors': semantic_errors,
        'terminalOutput': terminal_output
    })
@app.route('/executeCode', methods=['POST'])
def execute_code_route():
    data = request.json
    code = data.get('code', '')
    execution_id = data.get('executionId')
    user_input = data.get('userInput')
    if execution_id:
        print(f"Continuing execution {execution_id} with input: {user_input}")
    else:
        print(f"New code execution request of length {len(code)}")
    result = execute_code(code, execution_id, user_input)
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
if __name__ == '__main__':
    app.run(debug=True)