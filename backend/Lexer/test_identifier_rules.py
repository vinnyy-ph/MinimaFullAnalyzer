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

# Valid identifier test cases according to the rules
test_tokenization("var bi_Rth = 10;")     # Valid: starts with lowercase and contains valid chars
test_tokenization("var myVar123_ABC = 5;") # Valid: starts with lowercase and contains valid chars
test_tokenization("var Arg = 2;")          # Invalid: starts with uppercase, should split
test_tokenization("var _start = 3;")       # Invalid: starts with underscore, should split
test_tokenization("var 123abc = 4;")       # Invalid: starts with digit, should split
test_tokenization("var abc!def = 6;")      # Invalid: contains invalid char (!), should split
test_tokenization("test camelCase mixedCase PascalCase snake_case")  # Mixed cases
test_tokenization("var abcdefghijklmnopqrstuvwxyz = 7;") # Too long (26 chars) 