# code_generator.py
from lark import Visitor
import re

class CodeGenerator(Visitor):
    def __init__(self):
        super().__init__()
        self.output_code = []
        self.indentation = 0
        self.temp_var_counter = 0
        
    def get_temp_var(self):
        """Generate a unique temporary variable name"""
        self.temp_var_counter += 1
        return f"_temp_{self.temp_var_counter}"
        
    def add_line(self, line):
        """Add a line of Python code with proper indentation"""
        self.output_code.append("    " * self.indentation + line)
        
    def increase_indent(self):
        self.indentation += 1
        
    def decrease_indent(self):
        self.indentation = max(0, self.indentation - 1)
        
    def generate(self, tree):
        """Main entry point to generate code from the parse tree"""
        # Add standard imports and setup code
        self.output_code = [
            "# Generated Python code from Minima",
            "import sys",
            "",
            "# Runtime support functions",
            "def _minima_show(value):",
            "    print(value)",
            ""
        ]
        
        # Visit the tree to generate code
        self.visit(tree)
        
        # Return the generated code as a single string
        return "\n".join(self.output_code)
        
    def visit(self, tree):
        """Generic visit method that dispatches to specific visit methods"""
        if not hasattr(tree, "data"):
            return str(tree)
            
        method_name = f"visit_{tree.data}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(tree)
        else:
            # Default: visit all children
            results = []
            for child in tree.children:
                result = self.visit(child)
                if result is not None:
                    results.append(result)
            return "".join(results) if results else ""

    # Start with basic implementations - we'll expand these later
    def visit_start(self, node):
        """Visit the root node of the parse tree"""
        for child in node.children:
            self.visit(child)
        # Add a main guard to ensure code runs when executed
        self.add_line("")
        self.add_line("if __name__ == '__main__':")
        self.increase_indent()
        self.add_line("pass  # Main program has been processed above")
        self.decrease_indent()
        return None

    def visit_program(self, node):
        """Visit the program node (container for all statements)"""
        for child in node.children:
            self.visit(child)
        return None

    def visit_show_statement(self, node):
        """Generate code for show statements"""
        # The 3rd child (index 2) contains the expression to show
        expr_code = self.visit(node.children[2])
        self.add_line(f"_minima_show({expr_code})")
        return None

    def visit_expression(self, node):
        """Visit expression node"""
        return self.visit(node.children[0])

    def visit_literals(self, node):
        """Handle literal values (strings, numbers, etc.)"""
        token = node.children[0]
        if token.type == "TEXTLITERAL":
            # Text literals are in quotes already
            return token.value
        elif token.type in ("INTEGERLITERAL", "POINTLITERAL"):
            return token.value
        elif token.type in ("NEGINTEGERLITERAL", "NEGPOINTLITERAL"):
            # Remove the '~' and add a '-'
            return "-" + token.value[1:]
        elif token.type == "STATELITERAL":
            return "True" if token.value == "YES" else "False"
        elif token.type == "EMPTY":
            return "None"
        return str(token.value)
    
    # More visit methods for other node types will be added...
    # For now let's focus on expressions and variable declarations

    def visit_varlist_declaration(self, node):
        """Handle variable declarations"""
        identifier = node.children[1].value
        
        # Check if there's an initialization (var_init)
        if len(node.children) >= 3 and hasattr(node.children[2], "children"):
            # There's an initialization
            value_code = self.visit(node.children[2].children[1])
            self.add_line(f"{identifier} = {value_code}")
        else:
            # No initialization, use None
            self.add_line(f"{identifier} = None")
            
        # Handle additional variables in the list if present
        if len(node.children) > 3:
            self.visit(node.children[3])
        
        return None

    def visit_varlist_tail(self, node):
        """Handle additional variables in a variable list"""
        if not node.children:
            return None
            
        identifier = node.children[1].value
        
        # Check if there's an initialization
        if len(node.children) >= 3 and node.children[2]:
            # There's an initialization
            value_code = self.visit(node.children[2].children[1])
            self.add_line(f"{identifier} = {value_code}")
        else:
            # No initialization, use None
            self.add_line(f"{identifier} = None")
            
        # Handle additional variables in the list if present
        if len(node.children) > 3:
            self.visit(node.children[3])
            
        return None

    def visit_var_assign(self, node):
        """Handle variable assignments"""
        var_name = node.children[0].value
        
        # Check if it's a simple assignment or something more complex
        if len(node.children) >= 3:
            op = self.visit(node.children[2])
            if op in ["=", "+=", "-=", "*=", "/="]:
                value_code = self.visit(node.children[3])
                self.add_line(f"{var_name} {op} {value_code}")
            else:
                # Other operators, handle as needed
                value_code = self.visit(node.children[3])
                self.add_line(f"{var_name} {op} {value_code}")
                
        return None

    def visit_assign_op(self, node):
        """Convert assignment operators to Python equivalents"""
        return node.children[0].value

    def visit_logical_or_expr(self, node):
        """Handle logical OR expressions"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
            
        # Join all terms with OR operator
        terms = []
        for i in range(0, len(node.children), 2):
            terms.append(self.visit(node.children[i]))
            
        return " or ".join(terms)

    def visit_logical_and_expr(self, node):
        """Handle logical AND expressions"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
            
        # Join all terms with AND operator
        terms = []
        for i in range(0, len(node.children), 2):
            terms.append(self.visit(node.children[i]))
            
        return " and ".join(terms)

    def visit_equality_expr(self, node):
        """Handle equality comparison expressions"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
            
        # Handle both == and != operators
        left = self.visit(node.children[0])
        op = node.children[1].value
        right = self.visit(node.children[2])
        
        if op == "==":
            return f"({left} == {right})"
        else:  # op == "!="
            return f"({left} != {right})"

    def visit_relational_expr(self, node):
        """Handle relational comparison expressions"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
            
        # Handle <, <=, >, >= operators
        left = self.visit(node.children[0])
        op = node.children[1].value
        right = self.visit(node.children[2])
        
        return f"({left} {op} {right})"

    def visit_add_expr(self, node):
        """Handle addition and subtraction expressions"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
            
        # Handle + and - operators
        left = self.visit(node.children[0])
        op = node.children[1].value
        right = self.visit(node.children[2])
        
        return f"({left} {op} {right})"

    def visit_mul_expr(self, node):
        """Handle multiplication, division, and modulo expressions"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
            
        # Handle *, /, % operators
        left = self.visit(node.children[0])
        op = node.children[1].value
        right = self.visit(node.children[2])
        
        return f"({left} {op} {right})"

    def visit_pre_expr(self, node):
        """Handle unary operators like ! and ~"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
            
        op = node.children[0].value
        expr = self.visit(node.children[1])
        
        if op == "!":
            return f"(not {expr})"
        elif op == "~":
            return f"(-{expr})"
        
        return expr

    def visit_primary_expr(self, node):
        """Handle primary expressions"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
        else:
            # Handle parenthesized expressions
            return f"({self.visit(node.children[1])})"

    def visit_operand(self, node):
        """Handle operands"""
        return self.visit(node.children[0])

    def visit_id_usage(self, node):
        """Handle variable references"""
        var_name = node.children[0].value
        return var_name

    def visit_variable_value(self, node):
        """Handle variable values"""
        if not node.children:
            return "None"  # Empty case
            
        return self.visit(node.children[0])