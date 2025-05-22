# syntax_analyzer.py

import os
from lark import Lark, UnexpectedToken, UnexpectedCharacters, UnexpectedInput, UnexpectedEOF
from .syntax_errors import process_syntax_error
from .token_map import TOKEN_MAP

grammar_path = os.path.join(os.path.dirname(__file__), "grammar.lark")
parser = Lark.open(grammar_path, start="start", parser="lalr")

def analyze_syntax(code):
    # First, run the lexer to check for lexical errors
    from ..Lexer.minima_lexer import Lexer
    
    lexer = Lexer(code)
    tokens = lexer.tokenize_all()
    
    # Check if there are any lexical errors
    if lexer.errors:
        # Return the first lexical error as the main error
        first_error = lexer.errors[0]
        return (False, {
            "message": first_error.message,
            "rawMessage": first_error.message,
            "expected": [],
            "unexpected": "invalid token",
            "line": first_error.line,
            "column": first_error.column,
            "value": "",
            "type": "lexical",  # Mark as lexical error
            "keywords": [],
            "literals": [],
            "symbols": [],
            "others": [],
            "isEndOfInput": False
        })
    
    try:
        parse_tree = parser.parse(code)
        return (True, parse_tree)
    except (UnexpectedToken, UnexpectedCharacters, UnexpectedEOF, UnexpectedInput) as ut:
        expected_tokens = list(ut.expected) if hasattr(ut, "expected") else []
        token_val = ut.token if hasattr(ut, "token") and ut.token is not None else None
        processed_error = process_syntax_error(
            str(ut),
            ut.line if hasattr(ut, "line") else 0,
            ut.column if hasattr(ut, "column") else 0,
            expected_tokens,
            token_val,
            code
        )
        return (False, processed_error)