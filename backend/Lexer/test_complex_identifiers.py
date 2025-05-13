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

# Complex identifier test cases
test_tokenization("var x_123_abc = 10;")  # Valid identifier with underscores
test_tokenization("var _start = 5;")      # Invalid start with underscore
test_tokenization("var a_B_C_d = 20;")    # Mixed case with valid and invalid parts
test_tokenization("var ab123XYZ789 = 30;") # Mixed case numeric
test_tokenization("var multiple_Uppercase_Characters = 40;") # Multiple uppercase chars
test_tokenization("if (counter > 10) { var Result = true; }") # Mixed context with keywords
test_tokenization("var camelCase = 50;")  # camelCase with uppercase mid-word 