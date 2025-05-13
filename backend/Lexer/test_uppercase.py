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

# Test cases focusing on uppercase characters
test_tokenization("a_B_c")   # Should split into: 'a_' (valid), 'B' (invalid), '_c' (valid)
test_tokenization("abcDef")  # Should split into: 'abc' (valid), 'D' (invalid), 'ef' (valid)
test_tokenization("x123Y456") # Should split into: 'x123' (valid), 'Y' (invalid), '456' (valid)
test_tokenization("var Arg = 2;") # Should process 'A' as invalid, 'rg' as a valid identifier 