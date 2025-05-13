import sys
sys.path.append('.')
from backend.Lexer.minima_lexer import Lexer
from backend.Semantic.semantic_analyzer import SemanticAnalyzer
from backend.Syntax.syntax_analyzer import analyze_syntax
from backend.CodegenTAC.code_executor import execute_code

# Test full program with negative numbers and operations
test_program = """
# Negative literals and expressions
var a = -5;
var b = -3.14;

# Arithmetic with negative numbers
var c = a + b;
var d = a - b;
var e = a * b;
var f = a / b;

# Unary negation
var g = -a;
var h = -b;
var i = -(-a);

# Mixed expressions
var j = 10 - -5;
var k = -a * -b;
var l = -a / -b;

# Show results
show(a);
show(b);
show(c);
show(d);
show(e);
show(f);
show(g);
show(h);
show(i);
show(j);
show(k);
show(l);
"""

def run_semantic_analysis(code):
    """Run semantic analysis on code and return if successful"""
    print(f"Running semantic analysis...")
    
    # Run lexical and syntax analysis
    lexer = Lexer(code)
    tokens = lexer.tokenize_all()
    
    if lexer.errors:
        print("❌ Lexical errors:")
        for error in lexer.errors:
            print(f"  - {error.message}")
        return False
    
    success, result = analyze_syntax(code)
    if not success:
        print(f"❌ Syntax error: {result['message']}")
        return False
    
    # Run semantic analysis
    semantic_analyzer = SemanticAnalyzer()
    errors = semantic_analyzer.analyze(result)
    
    if errors:
        print("❌ Semantic errors:")
        for error in errors:
            print(f"  - {error.message}")
        return False
    
    print("✅ Semantic analysis successful")
    return True

def run_execution(code):
    """Run the code through the executor and return the results"""
    print(f"\nExecuting code...")
    
    results = execute_code(code)
    
    if not results['success']:
        print("❌ Execution failed:")
        print(f"  - {results['error']}")
        return False
    
    print("✅ Execution successful")
    print("\nOutput:")
    print("-------")
    print(results['output'])
    
    return True

print("===== COMPREHENSIVE NEGATIVE NUMBER TEST =====")
print("=============================================")

# First test semantic analysis
if run_semantic_analysis(test_program):
    # Then test execution
    run_execution(test_program)

print("\n=============================================")
print("Test complete.") 