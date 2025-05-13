import sys
sys.path.append('.')
from backend.Lexer.minima_lexer import Lexer

def test_tokenization(expr):
    print(f"\nTesting: '{expr}'")
    
    lexer = Lexer(expr)
    tokens = lexer.tokenize_all()
    
    print(f"Found {len(tokens)} tokens:")
    for i, token in enumerate(tokens):
        print(f"Token {i+1}: ({token.value}, {token.type})")

# Test long identifier
test_tokenization("var abcdefghijklmnopqrstuvwxyz = 7;") 