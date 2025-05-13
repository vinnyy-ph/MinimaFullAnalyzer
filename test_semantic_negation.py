import sys
sys.path.append('.')
from backend.Lexer.minima_lexer import Lexer
from backend.Semantic.semantic_analyzer import SemanticAnalyzer
from backend.Syntax.syntax_analyzer import analyze_syntax

# Test expressions that use negative numbers
test_expressions = [
    "var a = -5;",  
    "var b = -3.14;",
    "var c = a - b;",
    "var d = -a;",  # Unary negation
    "var e = -(-5);",  # Double negation
    "var f = 10 - -5;",  # Subtraction with negative literal
]

print("Testing semantic analysis of negative numbers:")
print("=============================================")

for expr in test_expressions:
    print(f"\nAnalyzing: '{expr}'")
    
    # Run lexical analysis
    lexer = Lexer(expr)
    tokens = []
    while True:
        token = lexer.get_next_token()
        if token is None:
            break
        tokens.append(token)
    
    if lexer.errors:
        print("❌ Lexical errors:")
        for error in lexer.errors:
            print(f"  - {error.message}")
        continue
    
    # Run syntax analysis
    success, result = analyze_syntax(expr)
    if not success:
        print(f"❌ Syntax error: {result['message']}")
        continue
    
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

print("\n=============================================")
print("Semantic analysis test complete.") 