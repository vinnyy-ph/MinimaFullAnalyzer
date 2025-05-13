import sys
sys.path.append('.')
from backend.Lexer.minima_lexer import Lexer
from backend.Semantic.semantic_analyzer import SemanticAnalyzer
from backend.Syntax.syntax_analyzer import analyze_syntax

# Simple expressions using literals first
test_expressions = [
    "var a = -5;",
    "var b = -3.14;",
    "var c = 10 - 5;",
    "var d = 10 - -5;",
    "var e = -(-5);",
]

def run_semantic_analysis(code):
    """Run full analysis pipeline on code and return semantic analyzer or None on error"""
    print(f"\nAnalyzing: '{code}'")
    
    # Run lexical and syntax analysis
    lexer = Lexer(code)
    tokens = lexer.tokenize_all()
    
    if lexer.errors:
        print("❌ Lexical errors:")
        for error in lexer.errors:
            print(f"  - {error.message}")
        return None
    
    success, result = analyze_syntax(code)
    if not success:
        print(f"❌ Syntax error: {result['message']}")
        return None
    
    # Run semantic analysis
    semantic_analyzer = SemanticAnalyzer()
    errors = semantic_analyzer.analyze(result)
    
    if errors:
        print("❌ Semantic errors:")
        for error in errors:
            print(f"  - {error.message}")
    else:
        print("✅ No semantic errors - expression is valid")
        
        # Show the variable values from the analysis
        for var_name, var_symbol in semantic_analyzer.global_scope.variables.items():
            var_value = getattr(var_symbol, "value", None)
            if var_value and isinstance(var_value, tuple) and len(var_value) >= 2:
                print(f"  {var_name}: {var_value[1]} ({var_value[0]})")
    
    return semantic_analyzer

print("Testing semantic analysis of negative numbers:")
print("=============================================")

for expr in test_expressions:
    analyzer = run_semantic_analysis(expr)

# Now test variable negation in a single context
combined_test = """
var x = 5;
var y = -x;
var z = -(-x);
"""

run_semantic_analysis(combined_test)

print("\n=============================================")
print("Semantic analysis test complete.") 