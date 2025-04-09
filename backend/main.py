from flask import Flask, request, jsonify
from flask_cors import CORS
from .Lexer.minima_lexer import Lexer  
from .Syntax.syntax_analyzer import analyze_syntax, parser
from .Semantic.semantic_analyzer import SemanticAnalyzer 
from .CodegenTAC.code_executor import execute_code, format_tac_instructions
import io
import sys
from contextlib import redirect_stdout

app = Flask(__name__)
CORS(app)

@app.route('/analyzeFull', methods=['POST'])
def analyze_full():
    data = request.get_json()
    code = data.get('code', '')

    # Capture stdout
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        # Lexical pass
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
                # Change from transform() to analyze()
                semantic_analyzer.analyze(parse_tree)
                semantic_errors = [error.to_dict() for error in semantic_analyzer.errors]
            else:
                # There is a syntax error
                syntax_errors = [result]

                # Force a semantic error entry so the tab shows (1)
                semantic_errors = [{
                    "type": "semantic",
                    "message": "Syntax errors detected. Resolve them before semantic analysis."
                }]
        else:
            # There are lexical errors
            syntax_errors = [{
                "type": "syntax",
                "message": "Lexical errors detected. Resolve them before syntax analysis."
            }]

            # Force a semantic error entry so the tab shows (1)
            semantic_errors = [{
                "type": "semantic",
                "message": "Lexical errors detected. Resolve them before syntax and semantic analysis."
            }]
    
    # Get the captured terminal output
    terminal_output = output_buffer.getvalue()

    return jsonify({
        'tokens': tokens,
        'lexicalErrors': lexical_errors,
        'syntaxErrors': syntax_errors,
        'semanticErrors': semantic_errors,
        'terminalOutput': terminal_output  # Add terminal output to response
    })

@app.route('/executeCode', methods=['POST'])
def execute_code_endpoint():
    """Endpoint to execute Minima code and return the results."""
    data = request.get_json()
    code = data.get('code', '')
    
    # Capture stdout for debug messages
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        # Execute the code
        results = execute_code(code)
    
    # Add debug terminal output
    results['terminalOutput'] = output_buffer.getvalue()
    
    # Format TAC instructions for readability
    if 'tac' in results and results['tac']:
        results['formattedTAC'] = format_tac_instructions(results['tac'])
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)