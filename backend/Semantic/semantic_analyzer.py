import re
from lark import Visitor
from .symbol_table import SymbolTable
from .semantic_errors import (
    InvalidListOperandError,
    ListIndexOutOfRangeError,
    SemanticError,
    FunctionRedefinedError,
    ParameterMismatchError,
    FunctionNotDefinedError,
    UndefinedIdentifierError,
    RedeclarationError,
    FixedVarReassignmentError,
    ControlFlowError,
    TypeMismatchError,
    UnreachableCodeError,
    InvalidListAccessError,
    InvalidGroupAccessError
)

# Helper conversion functions for state values.
def convert_state_to_int(state):
    # YES -> 1, NO -> 0
    return 1 if state == "YES" else 0

def convert_state_to_point(state):
    # YES -> 1.0, NO -> 0.0
    return 1.0 if state == "YES" else 0.0

class SemanticAnalyzer(Visitor):
    def __init__(self):
        super().__init__()
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.errors = []
        self.values = {}
        self.current_function = None
        self.loop_depth = 0
        self.switch_depth = 0
        self.in_loop_block = False
        self.has_return = False
        self.function_returns = {}  # Maps function names to their return values
        self.function_throw_expressions = {}  # Maps function names to their thrown expression nodes
        self.loop_stack = []  
        
    def push_scope(self):
        self.current_scope = SymbolTable(parent=self.current_scope)

    def pop_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def analyze(self, tree):
        """Main entry point to analyze the parse tree"""
        self.errors = []  # Clear previous semantic errors
        self.values = {}  # Optionally clear cached node values
        self.visit(tree)
        
        # Deduplicate errors
        unique_errors = []
        error_signatures = set()
        
        for error in self.errors:
            # Create a signature for each error using message + location
            signature = (error.message, error.line, error.column)
            if signature not in error_signatures:
                error_signatures.add(signature)
                unique_errors.append(error)
        
        self.errors = unique_errors
        return self.errors

    def visit(self, tree):
        if not hasattr(tree, "data"):
            # If it's a token, delegate to visit_token.
            if hasattr(tree, "type"):
                return self.visit_token(tree)
            else:
                return None
        method_name = f"visit_{tree.data}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(tree)
        else:
            # Default: visit all children.
            for child in tree.children:
                if hasattr(child, "data") or hasattr(child, "type"):
                    self.visit(child)
            return None

    def get_value(self, node):
        """Retrieve a value for a node, visiting it if needed"""
        if id(node) in self.values:
            return self.values[id(node)]
        
        if hasattr(node, 'data'):
            result = self.visit(node)
            return result
        elif hasattr(node, 'type'):  # It's a token
            return self.visit_token(node)
        return None

    def visit_token(self, token):
        """Visit a token and determine its value"""
        if token.type == 'TEXTLITERAL':
            result = ("text", token.value.strip('"'))
        elif token.type == 'INTEGERLITERAL':
            result = ("integer", int(token.value))
        elif token.type == 'NEGINTEGERLITERAL':
            result = ("integer", -int(token.value[1:]))
        elif token.type == 'POINTLITERAL':
            result = ("point", float(token.value))
        elif token.type == 'NEGPOINTLITERAL':
            result = ("point", -float(token.value[1:]))
        elif token.type == 'STATELITERAL':
            result = ("state", token.value)
        elif token.type == 'EMPTY':
            result = ("empty", None)
        else:
            result = token.value
        
        self.values[id(token)] = result
        return result

    ###############################
    # Expression Evaluation Logic #
    ###############################

    def infer_type_and_value(self, raw_value):
        """
        Manually infer type and value from a raw string literal.
        Expected formats:
          - Integer literal: "2"
          - Negative integer literal: "~2"
          - Floating point literal: "2.0"
          - Negative floating point literal: "~2.0"
          - Text literal: "\"string\""
          - State literal: "YES" or "NO"
          - Empty literal: "empty" (case-insensitive)
        """
        while hasattr(raw_value, "children") and len(raw_value.children) == 1:
            raw_value = raw_value.children[0]

        if hasattr(raw_value, "value"):
            s = raw_value.value.strip()
        else:
            s = str(raw_value).strip()

        # Debug: show the literal string being analyzed.
        print("infer_type_and_value received:", repr(s))

        if s.lower() == "empty":
            return "empty", None
        if s.startswith('"') and s.endswith('"'):
            return "text", s[1:-1]
        if s in ["YES", "NO"]:
            return ("state", s)

        m = re.fullmatch(r'^~(\d+)$', s)
        if m:
            return "integer", -int(m.group(1))
        m = re.fullmatch(r'^(\d+)$', s)
        if m:
            return "integer", int(m.group(1))
        m = re.fullmatch(r'^~(\d+\.\d+)$', s)
        if m:
            return "point", -float(m.group(1))
        m = re.fullmatch(r'^(\d+\.\d+)$', s)
        if m:
            return "point", float(m.group(1))
        return "unknown", None

    def extract_literal(self, node):
        """
        Drill down into a node to extract the actual literal.
        If the node is a Tree with data 'var_init' or 'variable_value',
        unwrap it to return the literal token.
        """
        if node is None:
            return None
            
        # NEW CODE: Check for expression with list access on non-list variables
        if hasattr(node, "data") and node.data == "expression":
            self._validate_expression_for_list_access(node)
        
        if hasattr(node, "data"):
            if node.data == "var_init":
                if node.children and len(node.children) >= 2:
                    return self.extract_literal(node.children[1])
                else:
                    return None
            if node.data == "variable_value":
                # Check if this is a GET operation
                if node.children and hasattr(node.children[0], "type") and node.children[0].type == "GET":
                    # For a GET operation, return the node itself so we can process it in get_value
                    return node
                # If this is a list literal, the first child is LSQB.
                if node.children and hasattr(node.children[0], "type") and node.children[0].type == "LSQB":
                    # Return the list_value node (child at index 1)
                    return self.extract_literal(node.children[1])
                else:
                    if node.children and len(node.children) >= 1:
                        return self.extract_literal(node.children[0])
                    else:
                        return None
        if isinstance(node, list):
            if not node:
                return None
            first = node[0]
            if (isinstance(first, str) and first == "=") or (hasattr(first, "value") and first.value == "="):
                if len(node) >= 2:
                    return self.extract_literal(node[1])
                else:
                    return None
            else:
                return self.extract_literal(first)
        return node

    def _validate_expression_for_list_access(self, node):
        """
        This method traverses an expression tree to find and validate any list access operations.
        It specifically looks for id_usage nodes that have group_or_list access on non-list variables.
        """
        # If this isn't a node with children, there's nothing to validate
        if not hasattr(node, "children"):
            return
            
        # If this is an operand/id_usage that accesses a variable
        if hasattr(node, "data") and (node.data == "id_usage" or node.data == "operand"):
            self._check_node_for_list_access(node)
        
        # Recursively check all children
        for child in node.children:
            self._validate_expression_for_list_access(child)

    def _check_node_for_list_access(self, node):
        """Helper to check if a node represents list access on a non-list variable."""
        if not hasattr(node, "children") or len(node.children) < 1:
            return
            
        # Get the variable name
        var_name = None
        if hasattr(node, "data") and node.data == "id_usage" and hasattr(node.children[0], "value"):
            var_name = node.children[0].value
        elif hasattr(node.children[0], "data") and node.children[0].data == "id_usage":
            var_name = node.children[0].children[0].value
        
        if not var_name:
            return
            
        # Look up the variable
        var_symbol = self.current_scope.lookup_variable(var_name)
        if not var_symbol:
            return  # Variable not found, other error handling will catch this
            
        # Get the variable's type
        var_value = getattr(var_symbol, "value", None)
        if not var_value or not isinstance(var_value, tuple):
            return
            
        var_type = var_value[0]
        
        # Check for list access on this node or its children
        for child in node.children:
            if (hasattr(child, "data") and child.data == "group_or_list" and 
                child.children and hasattr(child.children[0], "type")):
                # Found list access, check if variable is a list or text
                if child.children[0].type == "LSQB" and var_type != "list" and var_type != "text":
                    # This is list access on a non-list and non-text variable!
                    line = node.children[0].line if hasattr(node.children[0], "line") else 0
                    column = node.children[0].column if hasattr(node.children[0], "column") else 0
                    self.errors.append(InvalidListAccessError(var_name, line, column))
                    return
                # Check for group access on non-group
                elif child.children[0].type == "LBRACE" and var_type != "group":
                    # This is group access on a non-group!
                    line = node.children[0].line if hasattr(node.children[0], "line") else 0
                    column = node.children[0].column if hasattr(node.children[0], "column") else 0
                    self.errors.append(InvalidGroupAccessError(var_name, line, column))
                    return

    def visit_list_value(self, node):
        # 'items' contains the first expression and (optionally) the list_tail.
        children = node.children
        result = [self.get_value(children[0])]
        if len(children) > 1:
            # Second child is already a list of additional elements.
            list_tail = self.get_value(children[1])
            if isinstance(list_tail, list):
                result.extend(list_tail)
            else:
                result.append(list_tail)
        self.values[id(node)] = ("list", result)
        return ("list", result)

    def visit_list_tail(self, node):
        # Matches: COMMA, expression, and optionally another list_tail.
        children = node.children
        result = []
        if len(children) >= 2:
            result.append(self.get_value(children[1]))
        if len(children) == 3:
            # Third child is a list_tail that is already transformed to a list.
            list_tail = self.get_value(children[2])
            if isinstance(list_tail, list):
                result.extend(list_tail)
            else:
                result.append(list_tail)
        self.values[id(node)] = result
        return result

    # Helper to convert a value (with its type) to a numeric value for arithmetic.
    def to_numeric(self, typ, value, target="int"):
        if typ == "unknown":
            return 0  # Return a default numeric value for unknown types
        if typ == "state":
            return (float(convert_state_to_point(value)) if target == "point" 
                    else convert_state_to_int(value))
        elif typ == "integer":
            return value
        elif typ == "point":
            return value
        else:
            return 0

    def evaluate_binary(self, op, left, right, line=0, column=0):
        """
        Evaluate a binary arithmetic expression.
        left and right are tuples: (type, value)
        Returns a tuple (result_type, result_value)
        Enhanced to track get operations and be more permissive with user input.
        """
        # ENHANCED: Skip detailed type checking if either operand might involve user input
        # This check needs to be comprehensive and at the very beginning
        if (left[0] == "unknown" or right[0] == "unknown" or
            left[0] == "get" or right[0] == "get" or
            left[0] == "parameter" or right[0] == "parameter" or
            str(left[0]).startswith("g") or str(right[0]).startswith("g")):
            
            # For comparison operators, return a default state result
            if op in ["==", "!=", "<", ">", "<=", ">="]:
                return ("state", "NO")  # Default placeholder value for semantic analysis
            
            # For arithmetic, infer a reasonable type
            elif op in ["+", "-", "*", "/", "%"]:
                # If either operand is text (even if one is get/unknown), result is text for +
                if op == "+" and (left[0] == "text" or right[0] == "text"):
                    return ("text", "")  # Default empty text
                # Default to number types for other arithmetic
                elif op == "/":
                    return ("point", 0.0)  # Default point
                else:  # +, -, *, % default to integer
                    return ("integer", 0)  # Default integer
            
            # For other operations, be conservative
            else:
                return ("unknown", None)

        # # Existing code for has_gets
        # has_gets = []
        # if left[0] == "get":
        #     has_gets.append(left[1])
        # if right[0] == "get":
        #     has_gets.append(right[1])

        # if has_gets:
        #     return ("compound_get", has_gets)

        # Parameter type inference for operations
        if left[0] == "parameter" or right[0] == "parameter":
            if op in ["+", "-", "*", "/", "%"]:  # Arithmetic operations
                # For arithmetic operations, infer the result type
                if op == "/" or left[0] == "point" or right[0] == "point":
                    return ("point", 0.0)  # Use a default value instead of None
                else:
                    return ("integer", 0)  # Use a default value instead of None
            elif op in ["==", "!=", "<", ">", "<=", ">="]:  # Comparison operations
                return ("state", "NO")  # Use a default value
            else:
                # For other operations, be conservative
                return ("unknown", None)

        if left[0] == "empty" or right[0] == "empty":
            self.errors.append(SemanticError(
                f"Operator '{op}' not supported between '{left[0]}' and '{right[0]}'", line, column))
            return ("unknown", None)
        
        if left[0] == "list" or right[0] == "list":
            if op == "+":
                if left[0] == "list" and right[0] == "list":
                    return ("list", left[1] + right[1])
                else:
                    self.errors.append(SemanticError(
                        "Operator '+' not allowed between a list and a non-list", line, column))
                    return ("unknown", None)
            else:
                self.errors.append(SemanticError(
                    f"Operator '{op}' not allowed for list operands", line, column))
                return ("unknown", None)
        
        if op == "+" and (left[0] == "text" or right[0] == "text"):
            return ("text", str(left[1]) + str(right[1]))
        
        if left[0] == "text" or right[0] == "text":
            self.errors.append(SemanticError(
                f"Operator '{op}' not allowed on text type", line, column))
            return ("unknown", None)

        if left[0] == "empty" or right[0] == "empty":
            self.errors.append(SemanticError(
                f"Operator '{op}' not supported between '{left[0]}' and '{right[0]}'", line, column))
            return ("unknown", None)
        
        if left[0] == "list" or right[0] == "list":
            if op == "+":
                if left[0] == "list" and right[0] == "list":
                    return ("list", left[1] + right[1])
                else:
                    self.errors.append(SemanticError(
                        "Operator '+' not allowed between a list and a non-list", line, column))
                    return ("unknown", None)
            else:
                self.errors.append(SemanticError(
                    f"Operator '{op}' not allowed for list operands", line, column))
                return ("unknown", None)
        
        if op == "+" and (left[0] == "text" or right[0] == "text"):
            return ("text", str(left[1]) + str(right[1]))
        
        if left[0] == "text" or right[0] == "text":
            self.errors.append(SemanticError(
                f"Operator '{op}' not allowed on text type", line, column))
            return ("unknown", None)
        
        use_point = False
        if op == "/":
            use_point = True
        elif left[0] == "point" or right[0] == "point":
            use_point = True
        elif (left[0] == "state" and right[0] == "point") or (left[0] == "state" and right[0] == "state"):
            use_point = False
        
        L = self.to_numeric(left[0], left[1], "point" if use_point else "int")
        R = self.to_numeric(right[0], right[1], "point" if use_point else "int")
        result = None
        try:
            if op == "+":
                result = L + R
            elif op == "-":
                result = L - R
            elif op == "*":
                result = L * R
            elif op == "/":
                # Add division by zero check for concrete values
                if R == 0 or R == 0.0:
                     self.errors.append(SemanticError(
                         "Division by zero", line, column))
                     return ("unknown", None)
                result = L / R
            elif op == "%":
                 # Add division by zero check for concrete values
                if R == 0:
                     self.errors.append(SemanticError(
                         "Modulo by zero", line, column))
                     return ("unknown", None)
                result = L % R
            else:
                self.errors.append(SemanticError(
                    f"Unsupported operator '{op}'", line, column))
                return ("unknown", None)
        except Exception as e:
            self.errors.append(SemanticError(
                f"Error evaluating expression: {str(e)}", line, column))
            return ("unknown", None)
        
        if use_point:
            return ("point", result)
        else:
            return ("integer", result)
        
    def to_state(self, expr):
        typ, val = expr
        if typ == "empty":
            return False  # empty is considered falsy
        if typ == "state":
            return val == "YES"
        if typ == "integer":
            return val != 0
        if typ == "point":
            return val != 0.0
        if typ == "text":
            return val != ""
        return False

    ##############################
    # Visitor Methods (Expressions)
    ##############################
    def visit_expression(self, node):
        """
        Visit an expression node and check for list or group access patterns.
        This catches expressions like 'a[1]' and validates them.
        """
        # First get the result from the child node
        result = self.get_value(node.children[0])
        
        # Store the result for this node
        self.values[id(node)] = result
        
        # This is a critical new check for expressions used in variable declarations
        # If this expression contains an id_usage with list access on a non-list,
        # we need to scan for that pattern and report an error
        if result and isinstance(result, tuple) and len(result) > 0:
            # Recursively check for list/group access in this expression tree
            self._check_invalid_access_in_expr(node)
        
        return result

    def _check_invalid_access_in_expr(self, node):
        """
        Helper method to recursively check for invalid list/group access in an expression.
        """
        if not hasattr(node, "children"):
            return
            
        # If this is an id_usage node, check its children for list/group access
        if hasattr(node, "data") and node.data == "id_usage":
            var_name = node.children[0].value
            var_symbol = self.current_scope.lookup_variable(var_name)
            line = node.children[0].line
            column = node.children[0].column
            
            # Only continue if the variable exists
            if var_symbol:
                var_value = getattr(var_symbol, "value", None)
                if var_value and isinstance(var_value, tuple):
                    var_type = var_value[0]
                    
                    # Check children for list or group accessors
                    for child in node.children[1:]:
                        if hasattr(child, "data") and child.data == "group_or_list" and child.children:
                            accessor = child
                            
                            # Check if using list access on non-list
                            if accessor.children[0].type == "LSQB" and var_type != "list":
                                self.errors.append(InvalidListAccessError(
                                    var_name, line, column))
                            # Check if using group access on non-group
                            elif accessor.children[0].type == "LBRACE" and var_type != "group":
                                self.errors.append(InvalidGroupAccessError(
                                    var_name, line, column))
        
        # Recursively check all children
        for child in node.children:
            self._check_invalid_access_in_expr(child)

    def visit_logical_or_expr(self, node):
        children = node.children
        result = self.get_value(children[0])
        i = 1
        while i < len(children):
            op = children[i].value  # "||"
            right = self.get_value(children[i+1])
            result_bool = self.to_state(result) or self.to_state(right)
            result = ("state", "YES" if result_bool else "NO")
            i += 2
        self.values[id(node)] = result
        return result

    def visit_logical_and_expr(self, node):
        children = node.children
        result = self.get_value(children[0])
        i = 1
        while i < len(children):
            op = children[i].value  # "&&"
            right = self.get_value(children[i+1])
            result_bool = self.to_state(result) and self.to_state(right)
            result = ("state", "YES" if result_bool else "NO")
            i += 2
        self.values[id(node)] = result
        return result

    def visit_equality_expr(self, node):
        children = node.children
        if len(children) == 1:
            result = self.get_value(children[0])
        else:
            left = self.get_value(children[0])
            op = children[1].value  # "==" or "!="
            right = self.get_value(children[2])
    
            # UPDATED: More comprehensive check for get() results and user input
            if (left[0] == "unknown" or right[0] == "unknown" or 
                left[0] == "get" or right[0] == "get" or 
                left[0] == "parameter" or right[0] == "parameter" or
                str(left[0]).startswith("g") or str(right[0]).startswith("g") or
                left[1] is None or right[1] is None):  # Also be permissive with None values
                result = ("state", "NO")  # Default placeholder value
            elif left[0] == "empty" or right[0] == "empty":
                # Two empty values are equal to each other
                if op == "==":
                    comparison_result = (left[0] == "empty" and right[0] == "empty")
                else:  # op == "!="
                    comparison_result = (left[0] != "empty" or right[0] != "empty")
                result = ("state", "YES" if comparison_result else "NO")
            else:
                # Only perform comparison if neither is from get()
                try:
                    if op == "==":
                        comparison_result = left[1] == right[1]
                    else: # op == "!="
                        comparison_result = (left[1] != right[1])
                    result = ("state", "YES" if comparison_result else "NO")
                except TypeError as e:
                    line = children[1].line if hasattr(children[1], 'line') else 0
                    column = children[1].column if hasattr(children[1], 'column') else 0
                    self.errors.append(TypeMismatchError(
                        left[0], right[0], f"equality comparison ('{op}')", line, column))
                    result = ("unknown", None)
                except Exception as e:
                    line = children[1].line if hasattr(children[1], 'line') else 0
                    column = children[1].column if hasattr(children[1], 'column') else 0
                    self.errors.append(SemanticError(
                        f"Error in equality comparison: {str(e)}", line, column))
                    result = ("unknown", None)
    
            self.values[id(node)] = result
            return result

    def visit_relational_expr(self, node):
        children = node.children
        if len(children) == 1:
            result = self.get_value(children[0])
        else:
            left = self.get_value(children[0])
            op = children[1].value
            right = self.get_value(children[2])

            # Get line and column for error reporting
            line = children[1].line if hasattr(children[1], "line") else 0
            column = children[1].column if hasattr(children[1], "column") else 0

            # ENHANCED: More permissive check for get() operations and user input
            # Include any possibility where user input might be involved
            if (left[0] == "unknown" or right[0] == "unknown" or 
                left[0] == "get" or right[0] == "get" or 
                left[0] == "parameter" or right[0] == "parameter" or
                str(left[0]).startswith("g") or str(right[0]).startswith("g") or
                left[1] is None or right[1] is None):
                result = ("state", "NO")  # Default placeholder for semantic analysis

            # Add this debug code before the type checking
            print(f"DEBUG: left type={left[0]}, right type={right[0]}")
            
            # If there's an error, add further debugging
            if left[0] != "get" and right[0] != "get" and (str(left[0]).startswith("g") or str(right[0]).startswith("g")):
                print(f"DEBUG: Found partial 'get' match: {left[0]}, {right[0]}")

            # UPDATED: Better check for get() results using multiple approaches
            if (left[0] == "unknown" or right[0] == "unknown" or 
                left[0] == "get" or right[0] == "get" or 
                left[0] == "parameter" or right[0] == "parameter" or
                str(left[0]).startswith("g") or str(right[0]).startswith("g")):
                result = ("state", "NO")  # Default placeholder value for semantic analysis
            elif left[1] is None or right[1] is None:
                # Check if types are 'empty' before reporting error
                if left[0] != "empty" and right[0] != "empty":
                    self.errors.append(SemanticError(
                        f"Operator '{op}' not supported between '{left[0]}' and '{right[0]}'",
                        line, column))
                result = ("unknown", None) # Comparison with empty is generally not well-defined
            else:
                # Only perform comparison if both types are known and not get/unknown/parameter
                try:
                    if op == "<":
                        comparison = left[1] < right[1]
                    elif op == "<=":
                        comparison = left[1] <= right[1]
                    elif op == ">":
                        comparison = left[1] > right[1]
                    elif op == ">=":
                        comparison = left[1] >= right[1]
                    else:
                        self.errors.append(SemanticError(f"Unsupported relational operator '{op}'", line, column))
                        comparison = False
                    result = ("state", "YES" if comparison else "NO")
                except TypeError as e:
                    self.errors.append(TypeMismatchError(
                        left[0], right[0], f"relational comparison ('{op}')", line, column))
                    result = ("unknown", None)
                except Exception as e:
                    self.errors.append(SemanticError(
                        f"Error in comparison: {str(e)}", line, column))
                    result = ("unknown", None)
    
            self.values[id(node)] = result
            return result

    def visit_add_expr(self, node):
        children = node.children
        result = self.get_value(children[0])
        i = 1
        while i < len(children):
            op_token = children[i]
            op = op_token.value  # PLUS or MINUS
            right = self.get_value(children[i+1])
            result = self.evaluate_binary(op, result, right, op_token.line, op_token.column)
            i += 2
        self.values[id(node)] = result
        return result

    def visit_mul_expr(self, node):
        children = node.children
        result = self.get_value(children[0])
        i = 1
        while i < len(children):
            op_token = children[i]
            op = op_token.value  # STAR, SLASH, or PERCENT
            right = self.get_value(children[i+1])
            result = self.evaluate_binary(op, result, right, op_token.line, op_token.column)
            i += 2
        self.values[id(node)] = result
        return result

    def visit_pre_expr(self, node):
        children = node.children
        if len(children) == 1:
            result = self.get_value(children[0])
        else:
            op_token = children[0]
            expr = self.get_value(children[1])
            if op_token.value == "!":
                result_bool = not self.to_state(expr)
                result = ("state", "YES" if result_bool else "NO")
            elif op_token.value == "~":
                typ, val = expr
                if typ == "state":
                    # Convert "YES" to -1, "NO" to 0
                    result = ("integer", -convert_state_to_int(val))
                else:
                    result = (typ, -val)
        self.values[id(node)] = result
        return result

    def visit_primary_expr(self, node):
        children = node.children
        if len(children) == 1:
            result = self.get_value(children[0])
        else:
            result = self.get_value(children[1])
        self.values[id(node)] = result
        return result

    def visit_operand(self, node):
        result = self.get_value(node.children[0])
        self.values[id(node)] = result
        return result

    def visit_typecast_expression(self, node):
        children = node.children
        target_token = children[0]
        line = target_token.line
        column = target_token.column
        inner = self.get_value(children[2])
        target = target_token.value.lower()  # "integer", "point", "state", "text"
        
        # First extract the current type and value BEFORE using them
        if isinstance(inner, tuple) and len(inner) >= 2:
            current_type, current_value = inner[0], inner[1]
        else:
            current_type, current_value = "unknown", None
        
        # Now we can use current_type in conditions
        if current_type == "get" or str(current_type).startswith("g"):
            result = (target, None)  # Just assume the typecast will work at runtime
            self.values[id(node)] = result
            return result
        
        try:
            if target == "integer":
                if current_type == "point":
                    result = ("integer", int(current_value))
                elif current_type == "text":
                    result = ("integer", int(current_value))  # May raise ValueError
                elif current_type == "state":
                    result = ("integer", 1 if current_value == "YES" else 0)
                else:
                    result = inner
            elif target == "point":
                if current_type == "integer":
                    result = ("point", float(current_value))
                elif current_type == "text":
                    result = ("point", float(current_value))
                elif current_type == "state":
                    result = ("point", 1.0 if current_value == "YES" else 0.0)
                else:
                    result = inner
            elif target == "text":
                result = ("text", str(current_value))
            elif target == "state":
                if current_type in ("integer", "point"):
                    result = ("state", "YES" if current_value != 0 and current_value != 0.0 else "NO")
                elif current_type == "text":
                    result = ("state", "YES" if current_value != "" else "NO")
                else:
                    result = inner
            else:
                result = inner
        except ValueError as ve:
            error_str = str(ve)
            if "invalid literal for int()" in error_str:
                custom_msg = "Cannot convert provided text to integer."
            elif "could not convert string to float" in error_str:
                custom_msg = "Provided text is not a valid point."
            else:
                custom_msg = f"Error in typecasting: {error_str}"
            self.errors.append(SemanticError(custom_msg, line, column))
            result = ("unknown", None)
        except Exception as e:
            self.errors.append(SemanticError(f"Custom Error in typecasting: {str(e)}", line, column))
            result = ("unknown", None)
        
        self.values[id(node)] = result
        return result

    ##############################
    # Visitor Methods (Declarations, Assignments, etc.)
    ##############################

    def visit_varlist_declaration(self, node):
        children = node.children
        if len(children) < 2:
            return
        ident = children[1]
        line = ident.line
        column = ident.column
        name = ident.value
        
        if not self.current_scope.define_variable(name, fixed=False, line=line, column=column):
            self.errors.append(RedeclarationError(name, line, column))
            return

        if len(children) >= 3 and children[2] and not (hasattr(children[2], "type") and children[2].type == "SEMICOLON"):
            literal_node = self.extract_literal(children[2])
            if literal_node is not None:
                expr_value = self.get_value(literal_node)
                
                # Handle initialization based on expression type
                if isinstance(expr_value, tuple) and len(expr_value) >= 1:
                    if isinstance(expr_value, tuple) and len(expr_value) >= 1 and expr_value[0] == "get":
                        # Ensure we store it properly with exactly the "get" type string
                        self.current_scope.variables[name].value = ("get", expr_value[1])
                        # Print message for get operations
                        prompt_text = str(expr_value[1])
                        if self.current_function:
                            print(f"Declared variable {name} with get input and prompt \"{prompt_text}\" inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with get input and prompt \"{prompt_text}\"")
                    elif expr_value[0] == "compound_get":
                        prompts = expr_value[1]
                        prompt_texts = []
                        for p in prompts:
                            if isinstance(p, tuple) and len(p) >= 2:
                                prompt_texts.append(str(p[1]))
                            else:
                                prompt_texts.append("input")
                        
                        # Print message with multiple prompts
                        prompt_count = len(prompts)
                        prompts_str = " and ".join([f"'{pt}'" for pt in prompt_texts])
                        
                        if self.current_function:
                            print(f"Declared variable {name} with {prompt_count} get inputs and prompts {prompts_str} inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with {prompt_count} get inputs and prompts {prompts_str}")
                        
                        self.current_scope.variables[name].value = ("unknown", None)
                    else:
                        # Normal case (not a get operation)
                        if self.current_function:
                            print(f"Declared variable {name} inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                        self.current_scope.variables[name].value = expr_value
                else:
                    # Handle non-tuple case
                    if self.current_function:
                        print(f"Declared variable {name} inside function {self.current_function}")
                    else:
                        print(f"Declared global variable {name} with expression value {expr_value}")
                    self.current_scope.variables[name].value = expr_value
            else:
                if self.current_function:
                    print(f"Declared variable {name} inside function {self.current_function}")
                else:
                    print(f"Declared global variable {name} with empty value")
        else:
            if self.current_function:
                print(f"Declared variable {name} inside function {self.current_function}")
            else:
                print(f"Declared global variable {name} with empty value")
        
        # Process the varlist tail if present
        if len(children) > 3:
            self.visit(children[3])
        return


    def visit_varlist_tail(self, node):
        children = node.children
        if not children:
            return
        ident = children[1]
        line = ident.line
        column = ident.column
        name = ident.value
        if not self.current_scope.define_variable(name, fixed=False, line=line, column=column):
            self.errors.append(RedeclarationError(name, line, column))
            return
        if len(children) > 2 and children[2]:
            literal_node = self.extract_literal(children[2])
            if literal_node is not None:
                expr_value = self.get_value(literal_node)
                
                # Check if this is a single get operation or compound get operation
                if isinstance(expr_value, tuple) and len(expr_value) >= 1:
                    if isinstance(expr_value, tuple) and len(expr_value) >= 1 and expr_value[0] == "get":
                        # Ensure we store it properly with exactly the "get" type string
                        self.current_scope.variables[name].value = ("get", expr_value[1])
                        # Print message for get operations
                        prompt_text = str(expr_value[1])
                        if self.current_function:
                            print(f"Declared variable {name} with get input and prompt \"{prompt_text}\" inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with get input and prompt \"{prompt_text}\"")
                    elif expr_value[0] == "compound_get":
                        prompts = expr_value[1]
                        prompt_texts = []
                        for p in prompts:
                            if isinstance(p, tuple) and len(p) >= 2:
                                prompt_texts.append(str(p[1]))
                            else:
                                prompt_texts.append("input")
                        
                        # Print message with multiple prompts
                        prompt_count = len(prompts)
                        prompts_str = " and ".join([f"'{pt}'" for pt in prompt_texts])
                        
                        if self.current_function:
                            print(f"Declared variable {name} with {prompt_count} get inputs and prompts {prompts_str} inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with {prompt_count} get inputs and prompts {prompts_str}")
                        
                        self.current_scope.variables[name].value = ("unknown", None)
                    else:
                        # Normal case (not a get operation)
                        if self.current_function:
                            print(f"Declared variable {name} with expression value {expr_value[1]} and type {expr_value[0]} inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                        self.current_scope.variables[name].value = expr_value
                else:
                    # Handle non-tuple case
                    if self.current_function:
                        print(f"Declared variable {name} with expression value {expr_value} inside function {self.current_function}")
                    else:
                        print(f"Declared global variable {name} with expression value {expr_value}")
                    self.current_scope.variables[name].value = expr_value
            else:
                if self.current_function:
                    print(f"Declared variable {name} with empty value inside function {self.current_function}")
                else:
                    print(f"Declared global variable {name} with empty value")
        else:
            if self.current_function:
                print(f"Declared variable {name} with empty value inside function {self.current_function}")
            else:
                print(f"Declared global variable {name} with empty value")
        
        # Recursively process the next tail if it exists
        if len(children) > 3:
            self.visit(children[3])
        return


    def visit_fixed_declaration(self, node):
        children = node.children
        ident = children[1]
        line = ident.line
        column = ident.column
        name = ident.value
        if not self.current_scope.define_variable(name, fixed=True, line=line, column=column):
            self.errors.append(RedeclarationError(name, line, column))
            return
        if len(children) > 3 and children[3]:
            literal_node = self.extract_literal(children[3])
            if literal_node is not None:
                expr_value = self.get_value(literal_node)
                
                # Check if this is a get operation (single or compound)
                if isinstance(expr_value, tuple) and len(expr_value) >= 1:
                    if isinstance(expr_value, tuple) and len(expr_value) >= 1 and expr_value[0] == "get":
                        # Ensure we store it properly with exactly the "get" type string
                        self.current_scope.variables[name].value = ("get", expr_value[1])
                        # Print message for get operations
                        prompt_text = str(expr_value[1])
                        if self.current_function:
                            print(f"Declared fixed variable {name} with get input and prompt \"{prompt_text}\" inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with get input and prompt \"{prompt_text}\"")
                    elif expr_value[0] == "compound_get":
                        prompts = expr_value[1]
                        prompt_texts = []
                        for p in prompts:
                            if isinstance(p, tuple) and len(p) >= 2:
                                prompt_texts.append(str(p[1]))
                            else:
                                prompt_texts.append("input")
                        
                        # Print message with multiple prompts
                        prompt_count = len(prompts)
                        prompts_str = " and ".join([f"'{pt}'" for pt in prompt_texts])
                        
                        if self.current_function:
                            print(f"Declared fixed variable {name} with {prompt_count} get inputs and prompts {prompts_str} inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with {prompt_count} get inputs and prompts {prompts_str}")
                        
                        self.current_scope.variables[name].value = ("unknown", None)
                    else:
                        # Normal case (not a get operation)
                        if self.current_function:
                            print(f"Declared fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]} inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                        self.current_scope.variables[name].value = expr_value
                else:
                    # Handle non-tuple case
                    if self.current_function:
                        print(f"Declared fixed variable {name} with expression value {expr_value} inside function {self.current_function}")
                    else:
                        print(f"Declared global fixed variable {name} with expression value {expr_value}")
                    self.current_scope.variables[name].value = expr_value
            else:
                if self.current_function:
                    print(f"Declared fixed variable {name} with empty value inside function {self.current_function}")
                else:
                    print(f"Declared global fixed variable {name} with empty value")
        else:
            if self.current_function:
                print(f"Declared fixed variable {name} with empty value inside function {self.current_function}")
            else:
                print(f"Declared global fixed variable {name} with empty value")
        if len(children) > 4:
            self.visit(children[4])
        return

    def visit_fixed_tail(self, node):
        children = node.children
        if not children:
            return
        ident = children[1]
        line = ident.line
        column = ident.column
        name = ident.value
        if not self.current_scope.define_variable(name, fixed=True, line=line, column=column):
            self.errors.append(RedeclarationError(name, line, column))
            return
        if len(children) > 3 and children[3]:
            literal_node = self.extract_literal(children[3])
            if literal_node is not None:
                expr_value = self.get_value(literal_node)
                
                # Check if this is a get operation (single or compound)
                if isinstance(expr_value, tuple) and len(expr_value) >= 1:
                    if isinstance(expr_value, tuple) and len(expr_value) >= 1 and expr_value[0] == "get":
                        # Ensure we store it properly with exactly the "get" type string
                        self.current_scope.variables[name].value = ("get", expr_value[1])
                        # Print message for get operations
                        prompt_text = str(expr_value[1])
                        if self.current_function:
                            print(f"Declared fixed variable {name} with get input and prompt \"{prompt_text}\" inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with get input and prompt \"{prompt_text}\"")
                    elif expr_value[0] == "compound_get":
                        prompts = expr_value[1]
                        prompt_texts = []
                        for p in prompts:
                            if isinstance(p, tuple) and len(p) >= 2:
                                prompt_texts.append(str(p[1]))
                            else:
                                prompt_texts.append("input")
                        
                        # Print message with multiple prompts
                        prompt_count = len(prompts)
                        prompts_str = " and ".join([f"'{pt}'" for pt in prompt_texts])
                        
                        if self.current_function:
                            print(f"Declared fixed variable {name} with {prompt_count} get inputs and prompts {prompts_str} inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with {prompt_count} get inputs and prompts {prompts_str}")
                        
                        self.current_scope.variables[name].value = ("unknown", None)
                    else:
                        # Normal case (not a get operation)
                        if self.current_function:
                            print(f"Declared fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]} inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                        self.current_scope.variables[name].value = expr_value
                else:
                    # Handle non-tuple case
                    if self.current_function:
                        print(f"Declared fixed variable {name} with expression value {expr_value} inside function {self.current_function}")
                    else:
                        print(f"Declared global fixed variable {name} with expression value {expr_value}")
                    self.current_scope.variables[name].value = expr_value
            else:
                if self.current_function:
                    print(f"Declared fixed variable {name} with empty value inside function {self.current_function}")
                else:
                    print(f"Declared global fixed variable {name} with empty value")
        else:
            if self.current_function:
                print(f"Declared fixed variable {name} with empty value inside function {self.current_function}")
            else:
                print(f"Declared global fixed variable {name} with empty value")
        
        if len(children) > 4:
            self.visit(children[4])
        return


    def visit_var_assign(self, node):
        """
        Enhanced var_assign with support for list and group element reassignment.
        """
        children = node.children
        ident = children[0]
        line = ident.line
        column = ident.column
        name = ident.value
        
        # Find the scope containing the variable
        scope, symbol = self.current_scope.find_variable_scope(name)
        
        if symbol is None:
            self.errors.append(UndefinedIdentifierError(name, line, column))
            return
        
        if symbol.fixed:
            self.errors.append(FixedVarReassignmentError(name, line, column))
            return
        
        # Check for list or group access
        has_accessor = False
        accessor_node = None
        if len(children) > 1 and children[1] and hasattr(children[1], 'children') and children[1].children:
            has_accessor = True
            accessor_node = children[1]
            
            # Make the accessor aware of its parent
            accessor_node.parent = node
            
            # Visit to validate the accessor
            self.visit(accessor_node)
            
            # Check if variable is appropriate type for accessor
            var_value = getattr(symbol, "value", None)
            if var_value:
                var_type = var_value[0] if isinstance(var_value, tuple) else None
                
                # Check if using list access on non-list
                if accessor_node.children[0].type == "LSQB" and var_type != "list":
                    self.errors.append(InvalidListAccessError(
                        name, line, column))
                    return  # Exit early as this is a type error
                # Check if using group access on non-group
                elif accessor_node.children[0].type == "LBRACE" and var_type != "group":
                    self.errors.append(InvalidGroupAccessError(
                        name, line, column))
                    return  # Exit early as this is a type error
        
        # Extract the assignment operator
        assign_op_node = children[2]
        if hasattr(assign_op_node, 'data'):
            # It's a Tree node (e.g., assign_op), extract the token from its children
            op = assign_op_node.children[0].value
        else:
            # It's a token directly (shouldn't happen with this grammar)
            op = assign_op_node.value
        
        # For non-simple assignments, verify variable type is compatible
        if op != "=" and not has_accessor:
            var_value = getattr(symbol, "value", None)
            if var_value:
                var_type = var_value[0] if isinstance(var_value, tuple) else None
                
                if var_type not in ["integer", "point", "text"]:
                    self.errors.append(SemanticError(
                        f"Operator '{op}' not applicable to variable of type '{var_type}'", 
                        assign_op_node.children[0].line if hasattr(assign_op_node, 'children') else 0,
                        assign_op_node.children[0].column if hasattr(assign_op_node, 'children') else 0))
                    return  # Exit early as this is a type error
        
        # Get the value being assigned
        literal_node = self.extract_literal(children[3])
        expr_value = self.get_value(literal_node)
        
        # Update variable or list/group element
        if not has_accessor:
            # Simple variable assignment
            if op == "=":
                scope.variables[name].value =expr_value
            else:
                # Handle compound assignments (+=, -=, etc.)
                var_value = getattr(symbol, "value", None)
                if var_value:
                    # Compute the new value based on the operator
                    assign_token = assign_op_node.children[0] if hasattr(assign_op_node, "children") and assign_op_node.children else assign_op_node
                    line_info = assign_token.line
                    column_info = assign_token.column
                    if op == "+=":
                        new_value = self.evaluate_binary("+", var_value, expr_value, line_info, column_info)
                    elif op == "-=":
                        new_value = self.evaluate_binary("-", var_value, expr_value, line_info, column_info)
                    elif op == "*=":
                        new_value = self.evaluate_binary("*", var_value, expr_value, line_info, column_info)
                    elif op == "/=":
                        new_value = self.evaluate_binary("/", var_value, expr_value, line_info, column_info)
                    else:
                        new_value = expr_value  # Fallback
                        
                    scope.variables[name].value =new_value
                
            print(f"Variable {name} reassigned to expression value {expr_value[1]} and type {expr_value[0]}")
        else:
            # List/group element assignment
            var_value = getattr(symbol, "value", None)
            
            if var_value and isinstance(var_value, tuple) and len(var_value) > 1:
                var_type = var_value[0]
                
                if var_type == "list":
                    # List element assignment
                    # Get the index from the accessor
                    index_expr_node = accessor_node.children[1]
                    index_expr = self.get_value(index_expr_node)
                    
                    if index_expr[0] == "integer":
                        index = index_expr[1]
                        list_value = var_value[1]  # This is the list of values
                        
                        # Check index range
                        if index < 0 or index >= len(list_value):
                            # Get accurate line and column for error reporting
                            line = getattr(index_expr_node, 'line', 0)
                            column = getattr(index_expr_node, 'column', 0)
                            self.errors.append(ListIndexOutOfRangeError(
                                name, index, line, column))
                        else:
                            # Get the current element value
                            current_element = list_value[index]
                            
                            # Update the element based on the operator
                            if op == "=":
                                new_element_value = expr_value
                            else:
                                # Validate element type for compound assignments
                                if current_element[0] not in ["integer", "point", "text"]:
                                    self.errors.append(SemanticError(
                                        f"Operator '{op}' not applicable to element of type '{current_element[0]}'", 
                                        assign_op_node.line if hasattr(assign_op_node, 'line') else 0,
                                        assign_op_node.column if hasattr(assign_op_node, 'column') else 0))
                                    return
                                
                                # Compute the new value based on the operator
                                if op == "+=":
                                    new_element_value = self.evaluate_binary("+", current_element, expr_value)
                                elif op == "-=":
                                    new_element_value = self.evaluate_binary("-", current_element, expr_value)
                                elif op == "*=":
                                    new_element_value = self.evaluate_binary("*", current_element, expr_value)
                                elif op == "/=":
                                    new_element_value = self.evaluate_binary("/", current_element, expr_value)
                                else:
                                    new_element_value = expr_value  # Fallback
                            
                            # Update the list element
                            list_value[index] = new_element_value
                            # Update the variable with the modified list
                            scope.variables[name].value =("list", list_value)
                            
                            print(f"List element at index {index} reassigned to {new_element_value[1]} {new_element_value[0]}")
                
                elif var_type == "group":
                    # Group member assignment
                    # Get the key from the accessor
                    key_expr_node = accessor_node.children[1]
                    key_expr = self.get_value(key_expr_node)
                    
                    # Groups can have keys of type text, integer, state, or point
                    if key_expr[0] not in ["text", "integer", "state", "point"]:
                        line = getattr(key_expr_node, 'line', 0)
                        column = getattr(key_expr_node, 'column', 0)
                        self.errors.append(SemanticError(
                            f"Group key must be text, integer, or state, got {key_expr[0]}", 
                            line, column))
                        return
                    
                    group_members = var_value[1]  # List of (key, value) pairs
                    found = False
                    member_index = -1
                    
                    # Find the member with the matching key
                    for i, (k, v) in enumerate(group_members):
                        if k[0] == key_expr[0] and k[1] == key_expr[1]:
                            found = True
                            member_index = i
                            break
                    
                    if not found:
                        # Key not found - for dictionary-like behavior, we'll add the key
                        if op == "=":
                            # Add new key-value pair
                            group_members.append((key_expr, expr_value))
                            scope.variables[name].value =("group", group_members)
                            key_display = f'"{key_expr[1]}"' if key_expr[0] == "text" else str(key_expr[1])
                            print(f"Group member with key {key_display} added with value {expr_value[1]} {expr_value[0]}")
                        else:
                            # Cannot use compound operators on non-existent keys
                            line = getattr(key_expr_node, 'line', 0)
                            column = getattr(key_expr_node, 'column', 0)
                            self.errors.append(SemanticError(
                                f"Key '{key_expr[1]}' not found in group '{name}'", 
                                line, column))
                    else:
                        # Key found - update the existing value
                        current_value = group_members[member_index][1]
                        
                        # Update the value based on the operator
                        if op == "=":
                            new_value = expr_value
                        else:
                            # Validate element type for compound assignments
                            if current_value[0] not in ["integer", "point", "text"]:
                                self.errors.append(SemanticError(
                                    f"Operator '{op}' not applicable to element of type '{current_value[0]}'", 
                                    assign_op_node.line if hasattr(assign_op_node, 'line') else 0,
                                    assign_op_node.column if hasattr(assign_op_node, 'column') else 0))
                                return
                            
                            # Compute the new value based on the operator
                            if op == "+=":
                                new_value = self.evaluate_binary("+", current_value, expr_value)
                            elif op == "-=":
                                new_value = self.evaluate_binary("-", current_value, expr_value)
                            elif op == "*=":
                                new_value = self.evaluate_binary("*", current_value, expr_value)
                            elif op == "/=":
                                new_value = self.evaluate_binary("/", current_value, expr_value)
                            else:
                                new_value = expr_value  # Fallback
                        
                        # Update the group member
                        group_members[member_index] = (key_expr, new_value)
                        # Update the variable with the modified group
                        scope.variables[name].value =("group", group_members)
                        
                        # Format the key for display
                        key_display = f'"{key_expr[1]}"' if key_expr[0] == "text" else str(key_expr[1])
                        print(f"Group member with key {key_display} reassigned to {new_value[1]} {new_value[0]}")
        
        return
           
    def visit_id_usage(self, node):
        children = node.children
        ident = children[0]
        line = ident.line
        column = ident.column
        name = ident.value

        # Check if this is a function call
        if len(children) > 1 and hasattr(children[1], 'data') and children[1].data == "func_call":
            func_symbol = self.global_scope.lookup_function(name)
            if func_symbol is None:
                self.errors.append(FunctionNotDefinedError(name, line, column))
                result = ("unknown", None)
            else:
                expected = len(func_symbol.params)
                # Get the arguments
                arg_values = self.evaluate_function_args(children[1])
                provided = len(arg_values)
                
                if expected != provided:
                    self.errors.append(ParameterMismatchError(
                        name, expected, provided, line, column))
                    result = ("unknown", None)
                else:
                    # FIXED: First check if there's a throw expression to evaluate with parameters
                    if name in self.function_throw_expressions:
                        # Get the thrown expression
                        expr_node = self.function_throw_expressions[name]
                        
                        # Save the current scope and create a new one for function evaluation
                        old_scope = self.current_scope
                        self.push_scope()
                        
                        # Define parameters with argument values
                        for i, param_name in enumerate(func_symbol.params):
                            self.current_scope.define_variable(param_name, fixed=False)
                            self.current_scope.variables[param_name].value = arg_values[i]
                        
                        # Evaluate the thrown expression in this scope
                        result = self.get_value(expr_node)
                        
                        # Store the result for this specific call
                        self.function_returns[name] = result
                        
                        # Restore the previous scope
                        self.pop_scope()
                        
                        if isinstance(result, tuple) and len(result) >= 2:
                            print(f"Function call to '{name}' returns {result[1]} of type {result[0]}")
                        else:
                            print(f"Function call to '{name}' returns {result}")
                    elif name in self.function_returns:
                        # Only fallback to stored return value if no expression is available
                        result = self.function_returns[name]
                        if isinstance(result, tuple) and len(result) >= 2:
                            print(f"Function call to '{name}' returns {result[1]} of type {result[0]}")
                        else:
                            print(f"Function call to '{name}' returns {result}")
                    else:
                        # If no return value is stored, return empty
                        result = ("empty", None)
                        print(f"Function call to '{name}' throws value empty")
        else:
            # Look up the variable in the current scope - proper scope resolution
            symbol = self.current_scope.lookup_variable(name)
            if symbol is None:
                self.errors.append(UndefinedIdentifierError(name, line, column))
                result = ("unknown", None)
            else:
                result = getattr(symbol, "value", ("empty", None))

            # Check for group or list access and update result with the access result
            for child in children[1:]:
                if hasattr(child, "data"):
                    if child.data == "id_usagetail":
                        for subchild in child.children:
                            if hasattr(subchild, "data") and subchild.data == "group_or_list" and subchild.children:
                                subchild.parent = node  # ensure parent is set for error reporting in visit_group_or_list
                                # Visit the subchild to get the group/list element
                                access_result = self.visit(subchild)
                                # Update result with the access result if not None
                                if access_result is not None:
                                    result = access_result
                    elif child.data == "group_or_list" and child.children:
                        child.parent = node
                        # Visit the child to get the group/list element
                        access_result = self.visit(child)
                        # Update result with the access result if not None
                        if access_result is not None:
                            result = access_result

        self.values[id(node)] = result
        return result
        
    def visit_func_call(self, node):
        """
        Processes a function call.
        For semantic analysis we simply evaluate the arguments.
        """
        if len(node.children) > 1:
            args_node = node.children[1]
            args = []
            # The grammar for args: expression (COMMA expression)*
            if hasattr(args_node, 'data') and args_node.data == 'args':
                for child in args_node.children:
                    # Skip over COMMA tokens to avoid counting them as arguments.
                    if hasattr(child, 'type') and child.type == "COMMA":
                        continue
                    arg_val = self.get_value(child)
                    if arg_val is not None:
                        args.append(arg_val)
            self.values[id(node)] = args
        else:
            self.values[id(node)] = []
        return self.values[id(node)]

    def visit_func_definition(self, node):
        """
        Handles function definitions with syntax:
        func identifier(param1, param2) { function_prog }
        """
        # children: [FUNC, IDENTIFIER, LPAREN, param_node, RPAREN, LBRACE, function_prog, RBRACE, (optional SEMICOLON)]
        func_token = node.children[1]
        func_name = func_token.value
        line = func_token.line
        column = func_token.column

        # Extract parameters from the param node (node.children[3])
        params = []
        params_node = node.children[3]
        if hasattr(params_node, "children"):
            # Multiple parameters
            for child in params_node.children:
                if hasattr(child, "type") and child.type == "IDENTIFIER":
                    if child.value in params:
                        self.errors.append(SemanticError(
                            f"Parameter '{child.value}' is declared more than once in function '{func_name}'", child.line, child.column))
                    else:
                        params.append(child.value)
        else:
            # Single parameter case (params_node is likely a Token)
            if hasattr(params_node, "type") and params_node.type == "IDENTIFIER":
                params.append(params_node.value)

        # Define the function in the global scope; report error if redefined.
        if not self.global_scope.define_function(func_name, params=params, line=line, column=column):
            self.errors.append(FunctionRedefinedError(func_name, line, column))
            return

        # Print tracking message for function definition
        print(f'Function "{func_name}" defined with parameters {params}')

        # Save the current function context and enter a new scope for the function body (local scope)
        old_function = self.current_function
        old_has_return = self.has_return
        
        self.current_function = func_name
        self.has_return = False  # Reset return tracking for this function
        self.push_scope()

        # Define each parameter as a local variable in the new scope WITH PARAMETER TYPE
        # This is the key change - mark parameters as a special type
        for param in params:
            self.current_scope.define_variable(param, fixed=False)
            self.current_scope.variables[param].value = ("parameter", None)  # Mark as parameter type

        # Visit the function body; the body is in the "function_prog" child (index 6)
        self.visit(node.children[6])
        
        # AFTER visiting, check if a return value was set
        if not self.has_return and func_name not in self.function_returns:
            self.function_returns[func_name] = ("empty", None)
            print(f"Function '{func_name}' throws value empty")

        # Exit the function's local scope and restore the previous function context.
        self.pop_scope()
        self.current_function = old_function
        self.has_return = old_has_return

    def visit_function_prog(self, node):
        """
        Visits the function body (a block of statements inside the function).
        This is similar to the global program but runs in the function's local scope.
        """
        for child in node.children:
            self.visit(child)

    def visit_throw_statement(self, node):
        """
        Processes a throw statement - needs to be in a function.
        Syntax: THROW expression SEMICOLON
        Stores the expression for later evaluation when the function is called.
        """
        if not self.current_function:
            throw_token = node.children[0]
            line = throw_token.line
            column = throw_token.column
            self.errors.append(ControlFlowError(
                "throw", "functions", line, column))
            return None
        
        # Get expression being thrown
        expr_node = node.children[1]
        
        # Get the value of the expression
        result = self.get_value(expr_node)
        
        # Store the expression node for later evaluation during function calls
        self.function_throw_expressions[self.current_function] = expr_node
        
        # Also store the evaluated result for direct lookup
        self.function_returns[self.current_function] = result
        
        # Set that this function has a return value
        self.has_return = True
        
        print(f"Function '{self.current_function}' throws an expression/value")
        
        return None

    def evaluate_function_args(self, func_call_node):
        """
        Evaluates the arguments in a function call.
        Returns a list of (type, value) tuples.
        """
        args = []
        if len(func_call_node.children) > 1:
            args_node = func_call_node.children[1]
            
            if hasattr(args_node, 'data') and args_node.data == 'args':
                for child in args_node.children:
                    # Skip commas
                    if hasattr(child, 'type') and child.type == "COMMA":
                        continue
                    arg_val = self.get_value(child)
                    if arg_val is not None:
                        args.append(arg_val)
            elif hasattr(args_node, 'data') or hasattr(args_node, 'type'):
                # Single argument
                arg_val = self.get_value(args_node)
                if arg_val is not None:
                    args.append(arg_val)
        
        return args

    def visit_show_statement(self, node):
        """
        Semantic analysis for show_statement.
        Syntax: SHOW LPAREN expression RPAREN
        """
        # Visit the expression to evaluate it
        expr = node.children[2]
        expr_value = self.get_value(expr)
        return None

    def visit_control_flow(self, node):
        """
        Semantic analysis for control flow statements (EXIT, NEXT).
        These should only be used inside loops.
        """
        stmt_token = node.children[0]
        stmt_type = stmt_token.value.lower()  # "exit" or "next"
        line = stmt_token.line
        column = stmt_token.column
        
        if not self.in_loop_block:
            self.errors.append(ControlFlowError(
                stmt_type, "loops", line, column))
        return None

    def visit_variable_value(self, node):
        """
        Visit a variable_value node, which can be a list, an expression, or a GET operation.
        """
        children = node.children
        
        # Check if this is a GET operation
        if children and hasattr(children[0], "type") and children[0].type == "GET":
            # This is a get operation
            # The get_operand is the 3rd child (after LPAREN)
            if len(children) >= 3:
                # Get the prompt expression
                prompt_expr = self.get_value(children[2])
                
                # Create a special tuple indicating this is a get operation with the prompt
                result = ("get", prompt_expr)
                self.values[id(node)] = result
                return result
            
        # Handle other cases by recursively visiting children
        if not children:
            result = ("empty", None)
        elif hasattr(children[0], "type") and children[0].type == "LSQB":
            # List case
            result = self.get_value(children[1])
        else:
            # Expression case
            result = self.get_value(children[0])
        
        self.values[id(node)] = result
        return result

    def visit_get_operand(self, node):
        """
        Visit a get_operand node, which is the prompt inside a get() call.
        """
        if not node.children:
            # If there's no operand, return a default prompt
            return ("text", "Enter a value")
        
        # Otherwise, evaluate the expression inside
        return self.get_value(node.children[0])

    def handle_get_declaration(self, name, prompt):
        """
        Helper method to handle a variable declaration with a get() operation.
        """
        # Extract the prompt text from the prompt value
        prompt_text = "Enter a value"  # Default prompt
        
        if isinstance(prompt, tuple) and len(prompt) >= 2:
            # If prompt is a typed tuple like ("text", "enter input")
            prompt_type, prompt_value = prompt
            if prompt_type == "text" and isinstance(prompt_value, str):
                # For text prompts, use the string directly
                prompt_text = prompt_value
            elif prompt_value is not None:
                # For non-text prompts, convert to string
                prompt_text = str(prompt_value)
        
        # Print the declaration message with the extracted prompt text
        if self.current_function:
            print(f"Declared variable {name} with get input and prompt \"{prompt_text}\" inside function {self.current_function}")
        else:
            print(f"Declared global variable {name} with get input and prompt \"{prompt_text}\"")
        
        # Ensure we consistently return a "get" type, not "unknown"
        return ("get", prompt_text)

    def enter_loop(self):
        """Enter a loop context."""
        self.loop_depth += 1
        self.in_loop_block = True

    def exit_loop(self):
        """Exit a loop context."""
        self.loop_depth -= 1
        if self.loop_depth == 0:
            self.in_loop_block = False

    def enter_switch(self):
        """Enter a switch statement context."""
        self.switch_depth += 1

    def exit_switch(self):
        """Exit a switch statement context."""
        self.switch_depth -= 1
    
    def check_boolean_expr(self, expr_node, context):
        """
        Check if an expression node can be evaluated as a boolean (state).
        Used for conditional statements. Allow user input in conditions.
        """
        expr_value = self.get_value(expr_node)
        if not expr_value:
            # If expression evaluation failed completely, can't check type
            return
    
        # ENHANCED: Explicitly allow get, unknown, and parameter types in boolean contexts
        # Any type that might involve user input should be permitted in conditions
        allowed_types = ["state", "integer", "point", "text", "get", "unknown", "parameter"]
        
        # Also check for string representations that might indicate get() operations
        if expr_value[0] not in allowed_types and not str(expr_value[0]).startswith("g"):
            # Get line and column from the first token in the expression if possible
            line, column = 0, 0
            token_node = expr_node
            while hasattr(token_node, 'children') and token_node.children:
                token_node = token_node.children[0]

            if hasattr(token_node, 'line'):
                line = token_node.line
                column = token_node.column

            self.errors.append(TypeMismatchError(
                "state, integer, point, text, or user input", expr_value[0], context, line, column))
            
    def visit_each_statement(self, node):
        """
        Semantic analysis for each_statement (for loop).
        Syntax: EACH LPAREN each_initialization expression SEMICOLON (expression | var_assign) RPAREN LBRACE loop_block RBRACE
        """
        # Visit and validate the initialization
        self.visit(node.children[2])
        
        # Visit and validate the condition
        condition_expr = node.children[3]
        self.check_boolean_expr(condition_expr, "each loop condition")
        self.visit(condition_expr)
        
        # Visit and validate the increment
        self.visit(node.children[5])
        
        # Push scope and enter loop for the body
        self.push_scope()
        self.enter_loop()
        
        # Visit the loop body
        self.visit(node.children[7])  # loop_block
        
        # Exit loop and pop scope
        self.exit_loop()
        self.pop_scope()
        return None

    def visit_repeat_statement(self, node):
        """
        Semantic analysis for repeat_statement (while loop).
        Syntax: REPEAT LPAREN expression RPAREN LBRACE loop_block RBRACE
        """
        # Visit and validate the condition
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "repeat loop condition")
        self.visit(condition_expr)
        
        # Push scope and enter loop for the body
        self.push_scope()
        self.enter_loop()
        
        # Visit the loop body
        self.visit(node.children[4])  # loop_block
        
        # Exit loop and pop scope
        self.exit_loop()
        self.pop_scope()
        return None

    def visit_do_repeat_statement(self, node):
        """
        Semantic analysis for do_repeat_statement.
        Syntax: DO LBRACE loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        # Push scope and enter loop for the body
        self.push_scope()
        self.enter_loop()
        
        # Visit the loop body
        self.visit(node.children[2])
        
        # Visit and validate the condition
        condition_expr = node.children[6]
        self.check_boolean_expr(condition_expr, "do-repeat loop condition")
        self.visit(condition_expr)
        
        # Exit loop and pop scope
        self.exit_loop()
        self.pop_scope()
        return None

    def visit_checkif_statement(self, node):
        """
        Semantic analysis for checkif_statement (if statement).
        Syntax: CHECKIF LPAREN expression RPAREN LBRACE program RBRACE recheck_statement otherwise_statement
        """
        # Visit and validate the condition
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "checkif condition")
        self.visit(condition_expr)
        
        # Push scope for the if body
        self.push_scope()
        
        # Visit the if body
        self.visit(node.children[5])
        
        # Pop scope
        self.pop_scope()
        
        # Visit recheck (else if) and otherwise (else) statements if present
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                self.visit(child)
        
        return None

    def visit_recheck_statement(self, node):
        """
        Semantic analysis for recheck_statement (else if).
        Syntax: RECHECK LPAREN expression RPAREN LBRACE program RBRACE recheck_statement
        """
        children = node.children
        # Check that the expected children exist; otherwise, skip processing.
        if len(children) < 7:
            return None
    
        # Visit and validate the condition
        condition_expr = children[2]
        self.check_boolean_expr(condition_expr, "recheck condition")
        self.visit(condition_expr)
        
        # Push scope for the else-if body
        self.push_scope()
        
        # Visit the else-if body
        self.visit(children[5])
        
        # Pop scope
        self.pop_scope()
        
        # Visit nested recheck statement if present
        if len(children) > 7 and children[7]:
            self.visit(children[7])
        
        return None

    def visit_otherwise_statement(self, node):
        """
        Semantic analysis for otherwise_statement (else).
        Syntax: OTHERWISE LBRACE program RBRACE
        """
        # Check if the node has enough children before accessing them
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        # Push scope for the else body
        self.push_scope()
        
        # Visit the else body
        self.visit(node.children[2])
        
        # Pop scope
        self.pop_scope()
        
        return None

    def visit_switch_statement(self, node):
        """
        Semantic analysis for switch_statement.
        Syntax: SWITCH LPAREN expression RPAREN LBRACE CASE literals COLON program case_tail default RBRACE
        """
        # Visit the switch expression
        self.visit(node.children[2])
        
        # Push scope and enter switch context
        self.push_scope()
        self.enter_switch()
        
        # Track case values to detect duplicates
        case_values = set()
        
        # Process the first case
        case_value = self.get_value(node.children[6])
        if case_value and case_value[0] != "unknown":
            case_values.add(str(case_value))
        
        # Visit the first case body
        self.visit(node.children[8])
        
        # Process additional cases
        if len(node.children) > 9 and node.children[9]:
            self.visit_case_values(node.children[9], case_values)
        
        # Process default case if present
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])
        
        # Exit switch and pop scope
        self.exit_switch()
        self.pop_scope()
        
        return None

    def visit_case_values(self, case_tail_node, case_values):
        if not case_tail_node or not hasattr(case_tail_node, 'children'):
            return
        
        # Check if there are at least 2 children.
        if len(case_tail_node.children) < 2:
            return
    
        case_value = self.get_value(case_tail_node.children[1])
        if case_value and case_value[0] != "unknown":
            str_val = str(case_value)
            if str_val in case_values:
                # Find the line and column of the duplicate case
                line, column = 0, 0
                literal_token = case_tail_node.children[1]
                if hasattr(literal_token, 'line'):
                    line = literal_token.line
                    column = literal_token.column
                self.errors.append(SemanticError(
                    f"Duplicate case value: {case_value[1]}", line, column))
            else:
                case_values.add(str_val)
        
        # Visit the case body if it exists.
        if len(case_tail_node.children) >= 4:
            self.visit(case_tail_node.children[3])
        
        # Process nested case_tail if available.
        if len(case_tail_node.children) > 4 and case_tail_node.children[4]:
            self.visit_case_values(case_tail_node.children[4], case_values)

    def visit_group_or_list(self, node):
        if not node.children:
            return None

        # Determine if this is list access or group access
        is_list_access = node.children[0].type == "LSQB"
        # Evaluate the index/key expression
        index_expr = node.children[1]
        key_value = self.get_value(index_expr)

        # Retrieve the parent id_usage to know which variable is being accessed
        parent = getattr(node, 'parent', None)
        if parent and hasattr(parent, 'data') and parent.data == 'id_usage':
            var_name = parent.children[0].value
            var_symbol = self.current_scope.lookup_variable(var_name)
            if var_symbol:
                var_value = getattr(var_symbol, "value", None)
                if var_value:
                    var_type = var_value[0] if isinstance(var_value, tuple) else None

                    if is_list_access:
                        # NEW CONDITION: Handle text indexing
                        if var_type == "text":
                            # Text character indexing
                            text_value = var_value[1]
                            if key_value[0] == "integer":
                                idx = key_value[1]
                                if idx < 0 or idx >= len(text_value):
                                    # Get more accurate line and column information
                                    line = getattr(index_expr, 'line', 0)
                                    column = getattr(index_expr, 'column', 0)
                                    self.errors.append(SemanticError(
                                        f"Text index {idx} out of range for variable '{var_name}'", 
                                        line, column))
                                    result = ("unknown", None)
                                else:
                                    # Return the character at the specified index as a text type
                                    result = ("text", text_value[idx])
                                self.values[id(node)] = result
                                return result
                        elif var_type == "list":
                            # List index lookup
                            list_items = var_value[1]
                            if key_value[0] == "integer":
                                idx = key_value[1]
                                if idx < 0 or idx >= len(list_items):
                                    # Error handling...
                                    result = ("unknown", None)
                                else:
                                    # Return the actual element, not a wrapper
                                    result = list_items[idx]
                                self.values[id(node)] = result
                                return result
                        elif var_type != "list":
                            self.errors.append(InvalidListAccessError(
                                var_name, parent.children[0].line, parent.children[0].column))
                        else:
                            # Existing list index lookup logic
                            list_items = var_value[1]
                            if key_value[0] == "integer":
                                idx = key_value[1]
                                if idx < 0 or idx >= len(list_items):
                                    # Get more accurate line and column information
                                    line = getattr(index_expr, 'line', 0)
                                    column = getattr(index_expr, 'column', 0)
                                    self.errors.append(ListIndexOutOfRangeError(
                                        var_name, idx, line, column))
                                    result = ("unknown", None)
                                else:
                                    result = list_items[idx]
                                self.values[id(node)] = result
                                return result
                    else:  # Group access
                        # Existing group access logic remains unchanged
                        if var_type != "group":
                            self.errors.append(InvalidGroupAccessError(
                                var_name, parent.children[0].line, parent.children[0].column))
                        else:
                            # For a group, look up the key in the group members
                            group_members = var_value[1]  # List of (key, value) pairs
                            result = None
                            found = False

                            for k, v in group_members:
                                # Compare key types and values
                                if k[0] == key_value[0] and k[1] == key_value[1]:
                                    result = v
                                    found = True
                                    break

                            if not found:
                                # Get more accurate line and column information
                                line = getattr(index_expr, 'line', 0)
                                column = getattr(index_expr, 'column', 0)
                                self.errors.append(SemanticError(
                                    f"Key '{key_value[1]}' not found in group '{var_name}'",
                                    line, column))
                                result = ("unknown", None)
                            
                            self.values[id(node)] = result
                            return result
        # In case of missing parent or variable, return the evaluated key.
        self.values[id(node)] = key_value
        return key_value


    # In visit_group_declaration, replace the group declaration block with the following:
    
    def visit_group_declaration(self, node):
        ident = node.children[1]
        line = ident.line
        column = ident.column
        name = ident.value
        
        if not self.current_scope.define_variable(name, fixed=False, line=line, column=column):
            self.errors.append(RedeclarationError(name, line, column))
            return
        
        # Create a dict to track duplicate keys and a list to collect (key, value) pairs.
        group_data = {}
        group_members = []
        
        # Pass both to visit_group_members.
        self.visit_group_members(node.children[3], group_data, group_members)
        
        # Save the group value as a list of key-value pairs.
        self.current_scope.variables[name].value = ("group", group_members)
        
        # Print detailed information.
        print(f"Declared group {name} with {len(group_members)} members:")
        for key, value in group_members:
            # key and value are tuples like ("integer", 2) or ("text", "pair")
            print(f"{key[1]} ({key[0]}) : {value[1]} ({value[0]})")
        return
    
    # Now update visit_group_members to accept an extra parameter for the members list:
    
    def visit_group_members(self, node, group_data, group_members):
        if not node or not hasattr(node, 'children'):
            return
        
        # Process key-value pair
        key_expr = node.children[0]
        value_expr = node.children[2]
        
        key = self.get_value(key_expr)
        value = self.get_value(value_expr)
        
        # Only text, integer, point, and text can be keys
        if key[0] not in ["text", "integer", "state", "point"]:
            self.errors.append(SemanticError(
                f"Group key must be text, integer, or state, got {key[0]}",
                getattr(key_expr, 'line', 0), getattr(key_expr, 'column', 0)))
        else:
            # Use the string representation for duplicate detection
            str_key = str(key[1])
            if str_key in group_data:
                self.errors.append(SemanticError(
                    f"Duplicate key '{str_key}' in group",
                    getattr(key_expr, 'line', 0), getattr(key_expr, 'column', 0)))
            else:
                group_data[str_key] = True
                group_members.append((key, value))
        
        # Process member_tail if it exists.
        if len(node.children) > 3 and node.children[3]:
            self.visit_member_tail(node.children[3], group_data, group_members)
        return
    
    # Finally update visit_member_tail accordingly:
    
    def visit_member_tail(self, node, group_data, group_members):
        if not node or not hasattr(node, 'children') or len(node.children) < 2:
            return
        # Visit the nested group_members.
        self.visit_group_members(node.children[1], group_data, group_members)
        return

    # Function to visit the start rule
    def visit_start(self, node):
        for child in node.children:
            self.visit(child)
        return None

    # Function to visit the program rule
    def visit_program(self, node):
        for child in node.children:
            self.visit(child)
        return None
        
    # Visit loop block - handles control flow statements in loops
    def visit_loop_block(self, node):
        for child in node.children:
            self.visit(child)
        return None
        
    # Visit each loop in functions
    def visit_each_func_statement(self, node):
        # Similar to visit_each_statement but in a function context
        self.visit(node.children[2])
        condition_expr = node.children[3]
        self.check_boolean_expr(condition_expr, "each loop condition")
        self.visit(condition_expr)
        self.visit(node.children[5])
        
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[7])  # func_loop_block
        self.exit_loop()
        self.pop_scope()
        return None
        
    def visit_repeat_func_statement(self, node):
        # Similar to visit_repeat_statement but in a function context
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "repeat loop condition")
        self.visit(condition_expr)
        
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[4])  # func_loop_block
        self.exit_loop()
        self.pop_scope()
        return None
        
    def visit_do_repeat_func_statement(self, node):
        # Similar to visit_do_repeat_statement but in a function context
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[2])  # func_loop_block
        
        condition_expr = node.children[6]
        self.check_boolean_expr(condition_expr, "do-repeat loop condition")
        self.visit(condition_expr)
        
        self.exit_loop()
        self.pop_scope()
        return None
        
    def visit_func_loop_block(self, node):
        # Similar to visit_loop_block but can include throw statements
        for child in node.children:
            self.visit(child)
        return None
        
    # Handle conditional statements in loop contexts
    def visit_loop_checkif_statement(self, node):
        # Similar to visit_checkif_statement but in a loop context
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "checkif condition")
        self.visit(condition_expr)
        
        self.push_scope()
        self.visit(node.children[5])  # loop_block
        self.pop_scope()
        
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                self.visit(child)
        return None
        
    def visit_loop_recheck_statement(self, node):
        # Similar to visit_recheck_statement but in a loop context
        if not node or not hasattr(node, 'children') or len(node.children) < 7:
            return None
            
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "recheck condition")
        self.visit(condition_expr)
        
        self.push_scope()
        self.visit(node.children[5])  # loop_block
        self.pop_scope()
        
        if len(node.children) > 7 and node.children[7]:
            self.visit(node.children[7])
        return None
        
    def visit_loop_otherwise_statement(self, node):
        # Similar to visit_otherwise_statement but in a loop context
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        self.push_scope()
        self.visit(node.children[2])  # loop_block
        self.pop_scope()
        return None
        
    def visit_loop_switch_statement(self, node):
        # Similar to visit_switch_statement but in a loop context
        self.visit(node.children[2])  # expression
        
        self.push_scope()
        self.enter_switch()
        
        case_values = set()
        case_value = self.get_value(node.children[6])
        if case_value and case_value[0] != "unknown":
            case_values.add(str(case_value))
        
        self.visit(node.children[8])  # loop_block
        
        if len(node.children) > 9 and node.children[9]:
            self.visit_case_tail_loop(node.children[9], case_values)
        
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])  # loop_switch_default
        
        self.exit_switch()
        self.pop_scope()
        return None
        
    def visit_case_tail_loop(self, node, case_values):
        # Similar to visit_case_values but for loop context
        if not node or not hasattr(node, 'children'):
            return
        
        case_value = self.get_value(node.children[1])
        if case_value and case_value[0] != "unknown":
            str_val = str(case_value)
            if str_val in case_values:
                line = getattr(node.children[1], 'line', 0)
                column = getattr(node.children[1], 'column', 0)
                self.errors.append(SemanticError(
                    f"Duplicate case value: {case_value[1]}", line, column))
            else:
                case_values.add(str_val)
        
        self.visit(node.children[3])  # loop_block
        
        if len(node.children) > 4 and node.children[4]:
            self.visit_case_tail_loop(node.children[4], case_values)
        return

    # Handle conditional statements in function contexts
    def visit_func_checkif_statement(self, node):
        # Similar to visit_checkif_statement but in a function context
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "checkif condition")
        self.visit(condition_expr)
        
        self.push_scope()
        self.visit(node.children[5])  # function_prog
        self.pop_scope()
        
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                self.visit(child)
        return None
        
    def visit_func_recheck_statement(self, node):
        # Similar to visit_recheck_statement but in a function context
        if not node or not hasattr(node, 'children') or len(node.children) < 7:
            return None
            
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "recheck condition")
        self.visit(condition_expr)
        
        self.push_scope()
        self.visit(node.children[5])  # function_prog
        self.pop_scope()
        
        if len(node.children) > 7 and node.children[7]:
            self.visit(node.children[7])
        return None
        
    def visit_func_otherwise_statement(self, node):
        # Similar to visit_otherwise_statement but in a function context
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        self.push_scope()
        self.visit(node.children[2])  # function_prog
        self.pop_scope()
        return None
        
    def visit_func_switch_statement(self, node):
        # Similar to visit_switch_statement but in a function context
        self.visit(node.children[2])  # expression
        
        self.push_scope()
        self.enter_switch()
        
        case_values = set()
        case_value = self.get_value(node.children[6])
        if case_value and case_value[0] != "unknown":
            case_values.add(str(case_value))
        
        self.visit(node.children[8])  # function_prog
        
        if len(node.children) > 9 and node.children[9]:
            self.visit_func_case_tail(node.children[9], case_values)
        
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])  # func_switch_default
        
        self.exit_switch()
        self.pop_scope()
        return None
        
    def visit_func_case_tail(self, node, case_values):
        # Similar to visit_case_values but for function context
        if not node or not hasattr(node, 'children'):
            return
        
        case_value = self.get_value(node.children[1])
        if case_value and case_value[0] != "unknown":
            str_val = str(case_value)
            if str_val in case_values:
                line = getattr(node.children[1], 'line', 0)
                column = getattr(node.children[1], 'column', 0)
                self.errors.append(SemanticError(
                    f"Duplicate case value: {case_value[1]}", line, column))
            else:
                case_values.add(str_val)
        
        self.visit(node.children[3])  # function_prog
        
        if len(node.children) > 4 and node.children[4]:
            self.visit_func_case_tail(node.children[4], case_values)
        return
        
    # Handle conditional statements in function+loop contexts    
    def visit_func_loop_checkif_statement(self, node):
        # Handle if statements in a function loop context
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "checkif condition")
        self.visit(condition_expr)
        
        self.push_scope()
        self.visit(node.children[5])  # func_loop_block
        self.pop_scope()
        
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                self.visit(child)
        return None
        
    def visit_func_loop_recheck_statement(self, node):
        # Handle else-if statements in a function loop context
        if not node or not hasattr(node, 'children') or len(node.children) < 7:
            return None
            
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "recheck condition")
        self.visit(condition_expr)
        
        self.push_scope()
        self.visit(node.children[5])  # func_loop_block
        self.pop_scope()
        
        if len(node.children) > 7 and node.children[7]:
            self.visit(node.children[7])
        return None
        
    def visit_func_loop_otherwise_statement(self, node):
        # Handle else statements in a function loop context
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        self.push_scope()
        self.visit(node.children[2])  # func_loop_block
        self.pop_scope()
        return None
        
    def visit_func_loop_switch_statement(self, node):
        # Handle switch statements in a function loop context
        self.visit(node.children[2])  # expression
        
        self.push_scope()
        self.enter_switch()
        
        case_values = set()
        case_value = self.get_value(node.children[6])
        if case_value and case_value[0] != "unknown":
            case_values.add(str(case_value))
        
        self.visit(node.children[8])  # func_loop_block
        
        if len(node.children) > 9 and node.children[9]:
            self.visit_func_loop_case_tail(node.children[9], case_values)
        
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])  # func_loop_switch_default
        
        self.exit_switch()
        self.pop_scope()
        return None
        
    def visit_func_loop_case_tail(self, node, case_values):
        # Handle additional case statements in function loop switches
        if not node or not hasattr(node, 'children'):
            return
        
        case_value = self.get_value(node.children[1])
        if case_value and case_value[0] != "unknown":
            str_val = str(case_value)
            if str_val in case_values:
                line = getattr(node.children[1], 'line', 0)
                column = getattr(node.children[1], 'column', 0)
                self.errors.append(SemanticError(
                    f"Duplicate case value: {case_value[1]}", line, column))
            else:
                case_values.add(str_val)
        
        self.visit(node.children[3])  # func_loop_block
        
        if len(node.children) > 4 and node.children[4]:
            self.visit_func_loop_case_tail(node.children[4], case_values)
        return