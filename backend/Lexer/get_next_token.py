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

# Test our specific case
test_tokenization("a----5")  # Should be a(IDENTIFIER) --(--) -(-) -5(NEGINTEGERLITERAL)

# Test other related cases for comparison
test_tokenization("a---5")   # Should be a(IDENTIFIER) --(--) -(-) 5(INTEGERLITERAL)
test_tokenization("a--5")    # Should be a(IDENTIFIER) --(--) 5(INTEGERLITERAL) 