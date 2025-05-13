import sys
import os

# Add the project root directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.CodegenTAC.code_generator import TACGenerator
from backend.Lexer.minima_lexer import Lexer
from backend.Syntax.syntax_analyzer import analyze_syntax

def test_expression_precedence(code):
    """
    Test the TAC generation for an expression to verify precedence.
    """
    # Lex and parse the code
    lexer = Lexer(code)
    tokens = []
    while True:
        token = lexer.get_next_token()
        if token is None:
            break
        tokens.append(token)
    
    if lexer.errors:
        print("Lexical errors:", lexer.errors)
        return
    
    success, parse_tree_or_error = analyze_syntax(code)
    if not success:
        print("Syntax error:", parse_tree_or_error['message'])
        return
    
    parse_tree = parse_tree_or_error
    
    # Generate TAC with debug mode enabled
    code_generator = TACGenerator(debug_mode=True)
    tac_instructions = code_generator.generate(parse_tree)
    
    # Print the TAC instructions
    print("\nGenerated TAC:")
    for i, (op, arg1, arg2, result) in enumerate(tac_instructions):
        print(f"{i}: {op} {arg1}, {arg2}, {result}")
    
    return tac_instructions

if __name__ == "__main__":
    # Test various expressions with different precedence levels
    test_cases = [
        "var a = 1 + 2 * (3+3 / (5+5));\nshow(a);",  # The original example
        "var b = (5+5) * 2 + 1;\nshow(b);",         # Parentheses first
        "var c = 1 + 2 * 3;\nshow(c);",             # Simple precedence
        "var d = (1 + 2) * 3;\nshow(d);",           # Parentheses change precedence
        "var e = 10 / (2 + 3);\nshow(e);",          # Division with parentheses
        "var f = 10 / 2 + 3;\nshow(f);",            # Division without parentheses
    ]
    
    for i, test_code in enumerate(test_cases):
        print(f"\n=== Test Case {i+1} ===")
        print(f"Code: {test_code}")
        test_expression_precedence(test_code) 