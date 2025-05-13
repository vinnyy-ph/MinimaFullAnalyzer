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

# Test the specific case from the user
test_tokenization("var Arg = 2;")  # Should process 'A' as invalid, 'rg' as a valid identifier

# Test the original dash sequence cases
test_tokenization("a----5")  # Should be a(IDENTIFIER) --(--) -(-) -5(NEGINTEGERLITERAL)
test_tokenization("a---5")   # Should be a(IDENTIFIER) --(--) -(-) 5(INTEGERLITERAL)
test_tokenization("a--5")    # Should be a(IDENTIFIER) --(--) 5(INTEGERLITERAL)

# Test other edge cases for identifiers
test_tokenization("test1")   # Valid
test_tokenization("Test1")   # 'T' should be invalid, 'est1' should be valid
test_tokenization("a_B_c")   # 'a_' should be valid, 'B' invalid, '_c' valid
test_tokenization("var x1 = 123; var Y2 = 456;")  # Mixed valid/invalid 