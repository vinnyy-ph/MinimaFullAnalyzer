import sys
sys.path.append('.')
from backend.Lexer.minima_lexer import Lexer

def test_long_identifier():
    expr = "var abcdefghijklmnopqrstuvwxyz = 7;"
    print(f"\nTesting long identifier: '{expr}'")
    
    lexer = Lexer(expr)
    tokens = lexer.tokenize_all()
    
    print(f"Found {len(tokens)} tokens:")
    for i, token in enumerate(tokens):
        print(f"Token {i+1}: ({token.value}, {token.type}, error={token.error})")

    # Also print any collected errors
    print("\nErrors collected:")
    for error in lexer.errors:
        print(f"- {error.message} (line {error.line}, column {error.column})")

# Run the test
test_long_identifier() 