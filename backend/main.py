from flask import Flask, request, jsonify
from flask_cors import CORS
from .Lexer.minima_lexer import Lexer  
from .Syntax.syntax_analyzer import analyze_syntax, parser
from .Semantic.semantic_analyzer import SemanticAnalyzer 

app = Flask(__name__)
CORS(app)

@app.route('/analyzeFull', methods=['POST'])
def analyze_full():
    data = request.get_json()
    code = data.get('code', '')

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
            semantic_analyzer.transform(parse_tree)
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

    return jsonify({
        'tokens': tokens,
        'lexicalErrors': lexical_errors,
        'syntaxErrors': syntax_errors,
        'semanticErrors': semantic_errors
    })

if __name__ == '__main__':
    app.run(debug=True)
