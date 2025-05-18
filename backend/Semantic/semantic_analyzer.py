import re
from lark import Visitor
from .symbol_table import SymbolTable
from .semantic_errors import InvalidListOperandError, ListIndexOutOfRangeError, SemanticError, FunctionRedefinedError, ParameterMismatchError, FunctionNotDefinedError, UndefinedIdentifierError, RedeclarationError, FixedVarReassignmentError, ControlFlowError, TypeMismatchError, UnreachableCodeError, InvalidListAccessError, InvalidGroupAccessError, NegationError, BuiltinFunctionWithoutParensError
from ..CodegenTAC.built_in_functions import MinimaBultins
def convert_state_to_int(state):
    return 1 if state == "YES" else 0
def convert_state_to_point(state):
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
        self.match_depth = 0
        self.in_loop_block = False
        self.has_return = False
        self.function_returns = {}  
        self.function_throw_expressions = {}  
        self.loop_stack = []  
        self.builtin_functions = MinimaBultins.get_builtin_metadata()
        
        # Print the registered built-in functions for debugging
        print(f"Registered built-in functions: {list(self.builtin_functions.keys())}")
        
        # Add tracking for function scopes
        self.function_scopes = {}
    def push_scope(self):
        new_scope = SymbolTable(parent=self.current_scope)
        self.current_scope = new_scope
        
        # Track scopes created within functions
        if self.current_function:
            if self.current_function not in self.function_scopes:
                self.function_scopes[self.current_function] = []
            self.function_scopes[self.current_function].append(new_scope)
        
        return new_scope
    def pop_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
    def analyze(self, tree):
        """Main entry point to analyze the parse tree"""
        self.errors = []  
        self.values = {}  
        self.visit(tree)
        unique_errors = []
        error_signatures = set()
        for error in self.errors:
            signature = (error.message, error.line, error.column)
            if signature not in error_signatures:
                error_signatures.add(signature)
                unique_errors.append(error)
        self.errors = unique_errors
        return self.errors
    def visit(self, tree):
        if not hasattr(tree, "data"):
            if hasattr(tree, "type"):
                return self.visit_token(tree)
            else:
                return None
        method_name = f"visit_{tree.data}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(tree)
        else:
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
        elif hasattr(node, 'type'):  
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
    def infer_type_and_value(self, raw_value):
        """
        Manually infer type and value from a raw string literal.
        Expected formats:
          - Integer literal: "2"
          - Negative integer literal: "-2"
          - Floating point literal: "2.0"
          - Negative floating point literal: "-2.0"
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
        print("infer_type_and_value received:", repr(s))
        if s.lower() == "empty":
            return "empty", None
        if s.startswith('"') and s.endswith('"'):
            return "text", s[1:-1]
        if s in ["YES", "NO"]:
            return ("state", s)
        m = re.fullmatch(r'^-(\d+)$', s)
        if m:
            return "integer", -int(m.group(1))
        m = re.fullmatch(r'^(\d+)$', s)
        if m:
            return "integer", int(m.group(1))
        m = re.fullmatch(r'^-(\d+\.\d+)$', s)
        if m:
            return "point", -float(m.group(1))
        m = re.fullmatch(r'^(\d+\.\d+)$', s)
        if m:
            return "point", float(m.group(1))
        return "unknown", None
    def extract_literal(self, node):
        """
        Drill down into a node to find the core value node (literal, expression, list, get).
        If the node is 'var_init', get its value part.
        If the node is 'variable_value', return it if it's a list or GET, otherwise drill down.
        """
        if node is None:
            return None
        if hasattr(node, "data") and node.data == "var_init":
            if node.children and len(node.children) >= 2:
                return self.extract_literal(node.children[1])
            else:
                return None 
        if hasattr(node, "data") and node.data == "variable_value":
            if node.children and hasattr(node.children[0], "type"):
                if node.children[0].type == "GET" or node.children[0].type == "LSQB":
                    return node
            if node.children and len(node.children) >= 1:
                return self.extract_literal(node.children[0])
            else:
                return None 
        if hasattr(node, "data") and node.data == "expression":
             self._validate_expression_for_list_access(node)
             return node
        return node
    def _validate_expression_for_list_access(self, node):
        """
        This method traverses an expression tree to find and validate any list access operations.
        It specifically looks for id_usage nodes that have group_or_list access on non-list variables.
        """
        if not hasattr(node, "children"):
            return
        if hasattr(node, "data") and (node.data == "id_usage" or node.data == "operand"):
            self._check_node_for_list_access(node)
        for child in node.children:
            self._validate_expression_for_list_access(child)
    def _check_node_for_list_access(self, node):
        """Helper to check if a node represents list access on a non-list variable."""
        if not hasattr(node, "children") or len(node.children) < 1:
            return
        var_name = None
        if hasattr(node, "data") and node.data == "id_usage" and hasattr(node.children[0], "value"):
            var_name = node.children[0].value
        elif hasattr(node.children[0], "data") and node.children[0].data == "id_usage":
            if node.children[0].children and hasattr(node.children[0].children[0], "value"):
                 var_name = node.children[0].children[0].value
        if not var_name:
            return
        var_symbol = self.current_scope.lookup_variable(var_name)
        if not var_symbol:
            return  
        var_value = getattr(var_symbol, "value", None)
        if not var_value or not isinstance(var_value, tuple):
            return
        var_type = var_value[0]
        for child in node.children:
            if (hasattr(child, "data") and child.data == "group_or_list" and 
                child.children and hasattr(child.children[0], "type")):
                accessor_type = child.children[0].type
                line = node.children[0].line if hasattr(node.children[0], "line") else 0
                column = node.children[0].column if hasattr(node.children[0], "column") else 0
                if accessor_type == "LSQB":
                    allowed_types = ["list", "text", "parameter", "get", "unknown"]
                    if var_type not in allowed_types and not str(var_type).startswith("g"):
                        self.errors.append(InvalidListAccessError(var_name, line, column))
                        return
                elif accessor_type == "LBRACE":
                    allowed_types = ["group", "parameter", "get", "unknown"]
                    if var_type not in allowed_types and not str(var_type).startswith("g"):
                        self.errors.append(InvalidGroupAccessError(var_name, line, column))
                        return
    def visit_list_value(self, node):
        """Visit a list_value node, properly handling empty lists."""
        if not node.children:
            self.values[id(node)] = ("list", [])
            return ("list", [])
        children = node.children
        result = [self.get_value(children[0])]
        if len(children) > 1:
            list_tail = self.get_value(children[1])
            if isinstance(list_tail, list):
                result.extend(list_tail)
            else:
                result.append(list_tail)
        self.values[id(node)] = ("list", result)
        return ("list", result)
    def visit_list_tail(self, node):
        children = node.children
        result = []
        if len(children) >= 2:
            result.append(self.get_value(children[1]))
        if len(children) == 3:
            list_tail = self.get_value(children[2])
            if isinstance(list_tail, list):
                result.extend(list_tail)
            else:
                result.append(list_tail)
        self.values[id(node)] = result
        return result
    def to_numeric(self, typ, value, target="int"):
        if typ == "unknown":
            return 0  
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
        if (left[0] == "unknown" or right[0] == "unknown" or
            left[0] == "get" or right[0] == "get" or
            left[0] == "parameter" or right[0] == "parameter" or
            str(left[0]).startswith("g") or str(right[0]).startswith("g")):
            if op in ["==", "!=", "<", ">", "<=", ">="]:
                return ("state", "NO")  
            elif op in ["+", "-", "*", "/", "%"]:
                if op == "+" and (left[0] == "text" or right[0] == "text"):
                    return ("text", "")  
                elif op == "/":
                    return ("point", 0.0)  
                else:  
                    return ("integer", 0)  
            else:
                return ("unknown", None)
        if left[0] == "parameter" or right[0] == "parameter":
            if op in ["+", "-", "*", "/", "%"]:  
                if op == "/" or left[0] == "point" or right[0] == "point":
                    return ("point", 0.0)  
                else:
                    return ("integer", 0)  
            elif op in ["==", "!=", "<", ">", "<=", ">="]:  
                return ("state", "NO")  
            else:
                return ("unknown", None)
        if op == "+" and (left[0] == "text" or right[0] == "text"):
            return ("text", str(left[1]) + str(right[1]))
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
        original_L_was_none = False
        if L is None and left[0] in ["integer", "point", "state"]:
             original_L_was_none = True
             L = 0.0 if use_point else 0
        original_R_was_none = False
        if R is None and right[0] in ["integer", "point", "state"]:
             original_R_was_none = True
             R = 0.0 if use_point else 0
        result = None
        try:
            if op == "+":
                if left[0] == "text" or right[0] == "text":
                     L_str = str(left[1]) if left[1] is not None else ""
                     R_str = str(right[1]) if right[1] is not None else ""
                     if left[0] == "text" or right[0] == "text":
                         return ("text", L_str + R_str)
                result = L + R
            elif op == "-":
                result = L - R
            elif op == "*":
                result = L * R
            elif op == "/":
                # Check for division by zero
                if R == 0 or R == 0.0:
                    # More permissive check - if right side could be from function call or complex expression
                    if (original_R_was_none or 
                        isinstance(right[0], str) and (
                            right[0] in ["unknown", "parameter", "get"] or 
                            right[0].startswith("g") or
                            any(func in str(right[1]) for func in ["pow", "abs", "sum", "max", "min", "round", "ceil", "floor"])
                        )):
                        # Assume function calls or complex expressions will not yield zero at runtime
                        result = L / 1.0  # Use 1.0 as placeholder
                    else:
                        self.errors.append(SemanticError(
                            "Division by zero", line, column))
                        return ("point" if use_point else "integer", None)
                else:
                    result = L / R
            elif op == "%":
                # Check for modulo by zero
                if R == 0:
                    # More permissive check for modulo operations
                    if (original_R_was_none or 
                        isinstance(right[0], str) and (
                            right[0] in ["unknown", "parameter", "get"] or 
                            right[0].startswith("g") or
                            any(func in str(right[1]) for func in ["pow", "abs", "sum", "max", "min", "round", "ceil", "floor"])
                        )):
                        # Assume function calls or complex expressions will not yield zero at runtime
                        result = 0  # Use 0 as placeholder
                    else:
                        self.errors.append(SemanticError(
                            "Modulo by zero", line, column))
                        return ("integer", None)
                else:
                    result = L % R
            else:
                self.errors.append(SemanticError(
                    f"Unsupported operator '{op}'", line, column))
                return ("unknown", None)
        except TypeError as e:
             if "unsupported operand type(s)" in str(e) and (original_L_was_none or original_R_was_none):
                 print(f"Fallback: Caught TypeError after None handling for op '{op}'. L={L}, R={R}. Original types: {left[0]}, {right[0]}")
                 return ("integer" if not use_point else "point", None)
             else:
                 self.errors.append(SemanticError(
                     f"Type error during operation '{op}': {str(e)} between {left[0]} and {right[0]}", line, column))
                 return ("unknown", None)
        except Exception as e:
            self.errors.append(SemanticError(
                f"Error evaluating expression: {str(e)}", line, column))
            return ("unknown", None)
        result_value = None if original_L_was_none or original_R_was_none else result
        if use_point:
            return ("point", result_value)
        else:
            if op == '/' and not use_point:
                 return ("integer", int(result) if result_value is not None else None)
            return ("integer", int(result) if result_value is not None else None)
    def to_state(self, expr):
        typ, val = expr
        if typ == "empty":
            return False  
        if typ == "state":
            return val == "YES"
        if typ == "integer":
            return val != 0
        if typ == "point":
            return val != 0.0
        if typ == "text":
            return val != ""
        return False
    def visit_expression(self, node):
        """
        Visit an expression node and check for list or group access patterns.
        This catches expressions like 'a[1]' and validates them.
        """
        # Check if the expression directly contains a built-in function name
        if (len(node.children) > 0 and 
            hasattr(node.children[0], "children") and len(node.children[0].children) > 0 and
            hasattr(node.children[0].children[0], "type") and 
            node.children[0].children[0].type == "IDENTIFIER" and
            node.children[0].children[0].value in self.builtin_functions):
            
            func_name = node.children[0].children[0].value
            line = node.children[0].children[0].line
            column = node.children[0].children[0].column
            
            # Check if it's not being used as a function call
            has_func_call = False
            if (len(node.children[0].children) > 1 and 
                hasattr(node.children[0].children[1], "data") and 
                node.children[0].children[1].data == "func_call"):
                has_func_call = True
                
            if not has_func_call:
                self.errors.append(BuiltinFunctionWithoutParensError(func_name, line, column))
        
        result = self.get_value(node.children[0])
        self.values[id(node)] = result
        if result and isinstance(result, tuple) and len(result) > 0:
            self._check_invalid_access_in_expr(node)
        return result
    def _check_invalid_access_in_expr(self, node):
        """
        Helper method to recursively check for invalid list/group access in an expression.
        """
        if not hasattr(node, "children"):
            return
        if hasattr(node, "data") and node.data == "id_usage":
            var_name = node.children[0].value
            var_symbol = self.current_scope.lookup_variable(var_name)
            line = node.children[0].line
            column = node.children[0].column
            if var_symbol:
                var_value = getattr(var_symbol, "value", None)
                if var_value and isinstance(var_value, tuple):
                    var_type = var_value[0]
                    for child in node.children[1:]:
                        if hasattr(child, "data") and child.data == "group_or_list" and child.children:
                            accessor = child
                            if accessor.children[0].type == "LSQB" and var_type != "list":
                                self.errors.append(InvalidListAccessError(
                                    var_name, line, column))
                            elif accessor.children[0].type == "LBRACE" and var_type != "group":
                                self.errors.append(InvalidGroupAccessError(
                                    var_name, line, column))
        for child in node.children:
            self._check_invalid_access_in_expr(child)
    def visit_logical_or_expr(self, node):
        children = node.children
        result = self.get_value(children[0])
        i = 1
        while i < len(children):
            op = children[i].value  
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
            op = children[i].value  
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
            op = children[1].value  
            right = self.get_value(children[2])
            if (left[0] == "unknown" or right[0] == "unknown" or 
                left[0] == "get" or right[0] == "get" or 
                left[0] == "parameter" or right[0] == "parameter" or
                str(left[0]).startswith("g") or str(right[0]).startswith("g") or
                left[1] is None or right[1] is None):  
                result = ("state", "NO")  
            elif left[0] == "empty" or right[0] == "empty":
                if op == "==":
                    comparison_result = (left[0] == "empty" and right[0] == "empty")
                else:  
                    comparison_result = (left[0] != "empty" or right[0] != "empty")
                result = ("state", "YES" if comparison_result else "NO")
            else:
                try:
                    if op == "==":
                        comparison_result = left[1] == right[1]
                    else: 
                        comparison_result = left[1] != right[1]
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
            line = children[1].line if hasattr(children[1], "line") else 0
            column = children[1].column if hasattr(children[1], "column") else 0
            if (left[0] == "unknown" or right[0] == "unknown" or 
                left[0] == "get" or right[0] == "get" or 
                left[0] == "parameter" or right[0] == "parameter" or
                str(left[0]).startswith("g") or str(right[0]).startswith("g") or
                left[1] is None or right[1] is None):
                result = ("state", "NO")
            elif left[1] is None or right[1] is None:
                if left[0] != "empty" and right[0] != "empty":
                    self.errors.append(SemanticError(
                        f"Operator '{op}' not supported between '{left[0]}' and '{right[0]}'",
                        line, column))
                result = ("unknown", None) 
            else:
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
            op = op_token.value  
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
            op = op_token.value  
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
            elif op_token.value == "-":
                typ, val = expr if isinstance(expr, tuple) and len(expr) >= 2 else ("unknown", None)
                
                # Check if the type is a compound type (using the | separator)
                if typ and "|" in str(typ):
                    type_options = typ.split("|")
                    # Check if all possible types are numeric
                    if all(t in ["integer", "point"] for t in type_options):
                        # Since all options are numeric, negation is valid
                        result = (typ, -val if val is not None else None)
                    else:
                        # Not all types are numeric, report error
                        line = op_token.line if hasattr(op_token, 'line') else 0
                        column = op_token.column if hasattr(op_token, 'column') else 0
                        self.errors.append(NegationError(typ, line, column))
                        result = ("unknown", None)
                elif val is None:
                    result = ("unknown", None)
                elif typ == "state":
                    result = ("integer", -convert_state_to_int(val))
                elif typ in ["integer", "point"]:
                    result = (typ, -val)
                else:
                    # Report error for non-numeric types
                    line = op_token.line if hasattr(op_token, 'line') else 0
                    column = op_token.column if hasattr(op_token, 'column') else 0
                    self.errors.append(NegationError(typ, line, column))
                    result = ("unknown", None)
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
        # Check if this is a direct built-in function reference
        if (hasattr(node.children[0], 'type') and 
            node.children[0].type == 'IDENTIFIER' and 
            node.children[0].value in self.builtin_functions):
            
            func_name = node.children[0].value
            line = node.children[0].line if hasattr(node.children[0], 'line') else 0
            column = node.children[0].column if hasattr(node.children[0], 'column') else 0
            
            # Add error for using built-in function without parentheses
            self.errors.append(BuiltinFunctionWithoutParensError(func_name, line, column))
            result = ("unknown", None)
        else:
            result = self.get_value(node.children[0])
            
        self.values[id(node)] = result
        return result
    def visit_typecast_expression(self, node):
        children = node.children
        target_token = children[0]
        line = target_token.line
        column = target_token.column
        inner = self.get_value(children[2])
        target = target_token.value.lower()  
        if isinstance(inner, tuple) and len(inner) >= 2:
            current_type, current_value = inner[0], inner[1]
        else:
            current_type, current_value = "unknown", None
        if current_type == "get" or str(current_type).startswith("g"):
            result = (target, None)  
            self.values[id(node)] = result
            return result
        try:
            if target == "integer":
                if current_type == "point":
                    result = ("integer", int(current_value))
                elif current_type == "text":
                    result = ("integer", int(current_value))  
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
            # Check if we might be using a built-in function name directly
            if (hasattr(children[2], "children") and len(children[2].children) > 0 and
                hasattr(children[2].children[0], "type") and 
                children[2].children[0].type == "IDENTIFIER" and
                children[2].children[0].value in self.builtin_functions):
                
                func_name = children[2].children[0].value
                line = children[2].children[0].line
                column = children[2].children[0].column
                
                # Check it's not used as a function call
                has_func_call = False
                if (len(children[2].children) > 1 and 
                    hasattr(children[2].children[1], "data") and 
                    children[2].children[1].data == "func_call"):
                    has_func_call = True
                
                if not has_func_call:
                    self.errors.append(BuiltinFunctionWithoutParensError(func_name, line, column))
            
            literal_node = self.extract_literal(children[2])
            if literal_node is not None:
                expr_value = self.get_value(literal_node)
                if isinstance(expr_value, tuple) and len(expr_value) >= 1:
                    if isinstance(expr_value, tuple) and len(expr_value) >= 1 and expr_value[0] == "get":
                        self.current_scope.variables[name].value = ("get", expr_value[1])
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
                        prompt_count = len(prompts)
                        prompts_str = " and ".join([f"'{pt}'" for pt in prompt_texts])
                        if self.current_function:
                            print(f"Declared variable {name} with {prompt_count} get inputs and prompts {prompts_str} inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with {prompt_count} get inputs and prompts {prompts_str}")
                        self.current_scope.variables[name].value = ("unknown", None)
                    else:
                        if self.current_function:
                            print(f"Declared variable {name} inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                        self.current_scope.variables[name].value = expr_value
                else:
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
                if isinstance(expr_value, tuple) and len(expr_value) >= 1:
                    if isinstance(expr_value, tuple) and len(expr_value) >= 1 and expr_value[0] == "get":
                        self.current_scope.variables[name].value = ("get", expr_value[1])
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
                        prompt_count = len(prompts)
                        prompts_str = " and ".join([f"'{pt}'" for pt in prompt_texts])
                        if self.current_function:
                            print(f"Declared variable {name} with {prompt_count} get inputs and prompts {prompts_str} inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with {prompt_count} get inputs and prompts {prompts_str}")
                        self.current_scope.variables[name].value = ("unknown", None)
                    else:
                        if self.current_function:
                            print(f"Declared variable {name} with expression value {expr_value[1]} and type {expr_value[0]} inside function {self.current_function}")
                        else:
                            print(f"Declared global variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                        self.current_scope.variables[name].value = expr_value
                else:
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
            # Check if we might be using a built-in function name directly
            if (hasattr(children[3], "children") and len(children[3].children) > 0 and
                hasattr(children[3].children[0], "type") and 
                children[3].children[0].type == "IDENTIFIER" and
                children[3].children[0].value in self.builtin_functions):
                
                func_name = children[3].children[0].value
                line = children[3].children[0].line
                column = children[3].children[0].column
                
                # Check it's not used as a function call
                has_func_call = False
                if (len(children[3].children) > 1 and 
                    hasattr(children[3].children[1], "data") and 
                    children[3].children[1].data == "func_call"):
                    has_func_call = True
                
                if not has_func_call:
                    self.errors.append(BuiltinFunctionWithoutParensError(func_name, line, column))
            
            literal_node = self.extract_literal(children[3])
            if literal_node is not None:
                expr_value = self.get_value(literal_node)
                if isinstance(expr_value, tuple) and len(expr_value) >= 1:
                    if isinstance(expr_value, tuple) and len(expr_value) >= 1 and expr_value[0] == "get":
                        self.current_scope.variables[name].value = ("get", expr_value[1])
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
                        prompt_count = len(prompts)
                        prompts_str = " and ".join([f"'{pt}'" for pt in prompt_texts])
                        if self.current_function:
                            print(f"Declared fixed variable {name} with {prompt_count} get inputs and prompts {prompts_str} inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with {prompt_count} get inputs and prompts {prompts_str}")
                        self.current_scope.variables[name].value = ("unknown", None)
                    else:
                        if self.current_function:
                            print(f"Declared fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]} inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                        self.current_scope.variables[name].value = expr_value
                else:
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
                if isinstance(expr_value, tuple) and len(expr_value) >= 1:
                    if isinstance(expr_value, tuple) and len(expr_value) >= 1 and expr_value[0] == "get":
                        self.current_scope.variables[name].value = ("get", expr_value[1])
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
                        prompt_count = len(prompts)
                        prompts_str = " and ".join([f"'{pt}'" for pt in prompt_texts])
                        if self.current_function:
                            print(f"Declared fixed variable {name} with {prompt_count} get inputs and prompts {prompts_str} inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with {prompt_count} get inputs and prompts {prompts_str}")
                        self.current_scope.variables[name].value = ("unknown", None)
                    else:
                        if self.current_function:
                            print(f"Declared fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]} inside function {self.current_function}")
                        else:
                            print(f"Declared global fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                        self.current_scope.variables[name].value = expr_value
                else:
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
        
        # Check if we're trying to assign a built-in function name without parentheses 
        assign_op_node = children[2]
        if hasattr(assign_op_node, 'data'):
            op = assign_op_node.children[0].value
        else:
            op = assign_op_node.value
            
        # If we have something like "a = length" in the rhs
        if (len(children) > 3 and isinstance(children[3], object) and 
            hasattr(children[3], 'children') and len(children[3].children) > 0 and
            hasattr(children[3].children[0], 'type') and children[3].children[0].type == 'IDENTIFIER'):
            
            rhs_id = children[3].children[0].value
            if rhs_id in self.builtin_functions:
                rhs_line = children[3].children[0].line
                rhs_column = children[3].children[0].column
                self.errors.append(BuiltinFunctionWithoutParensError(rhs_id, rhs_line, rhs_column))
        
        scope, symbol = self.current_scope.find_variable_scope(name)
        if symbol is None:
            self.errors.append(UndefinedIdentifierError(name, line, column))
            return
        if symbol.fixed:
            self.errors.append(FixedVarReassignmentError(name, line, column))
            return
            
        # Rest of the existing code
        has_accessor = False
        accessor_node = None
        if len(children) > 1 and children[1] and hasattr(children[1], 'children') and children[1].children:
            has_accessor = True
            accessor_node = children[1]
            accessor_node.parent = node
            self.visit(accessor_node)
            var_value = getattr(symbol, "value", None)
            if var_value:
                var_type = var_value[0] if isinstance(var_value, tuple) else None
                if accessor_node.children[0].type == "LSQB" and var_type != "list":
                    self.errors.append(InvalidListAccessError(
                        name, line, column))
                    return  
                elif accessor_node.children[0].type == "LBRACE" and var_type != "group":
                    self.errors.append(InvalidGroupAccessError(
                        name, line, column))
                    return  

        if op != "=" and not has_accessor:
            var_value = getattr(symbol, "value", None)
            if var_value:
                var_type = var_value[0] if isinstance(var_value, tuple) else None
                if op == "+=" and var_type == "list":
                    pass
                elif var_type not in ["integer", "point", "text"]:
                    self.errors.append(SemanticError(
                        f"Operator '{op}' not applicable to variable of type '{var_type}'", 
                        assign_op_node.children[0].line if hasattr(assign_op_node, 'children') else 0,
                        assign_op_node.children[0].column if hasattr(assign_op_node, 'children') else 0))
                    return  
        literal_node = self.extract_literal(children[3])
        expr_value = self.get_value(literal_node)
        if not has_accessor:
            if op == "=":
                scope.variables[name].value = expr_value
            else:
                var_value = getattr(symbol, "value", None)
                if var_value:
                    assign_token = assign_op_node.children[0] if hasattr(assign_op_node, "children") and assign_op_node.children else assign_op_node
                    line_info = getattr(assign_token, 'line', 0)
                    column_info = getattr(assign_token, 'column', 0)
                    if op == "+=" and var_value[0] == "list":
                        if expr_value[0] == "list":
                            var_list = var_value[1]
                            expr_list = expr_value[1]
                            var_list.extend(expr_list)
                            scope.variables[name].value = ("list", var_list)
                            print(f"List {name} extended in-place with {len(expr_list)} elements")
                        else:
                            self.errors.append(SemanticError(
                                f"Can only concatenate list to list (not '{expr_value[0]}')", 
                                line_info, column_info))
                    else:
                        if op == "+=":
                            new_value = self.evaluate_binary("+", var_value, expr_value, line_info, column_info)
                        elif op == "-=":
                            new_value = self.evaluate_binary("-", var_value, expr_value, line_info, column_info)
                        elif op == "*=":
                            new_value = self.evaluate_binary("*", var_value, expr_value, line_info, column_info)
                        elif op == "/=":
                            new_value = self.evaluate_binary("/", var_value, expr_value, line_info, column_info)
                        else:
                            new_value = expr_value  
                        scope.variables[name].value = new_value
                print(f"Variable {name} reassigned to expression value {expr_value[1]} and type {expr_value[0]}")
        else:
            # Rest of the existing code for accessors...
            var_value = getattr(symbol, "value", None)
            if var_value and isinstance(var_value, tuple) and len(var_value) > 1:
                var_type = var_value[0]
                if var_type == "list":
                    index_expr_node = accessor_node.children[1]
                    index_expr = self.get_value(index_expr_node)
                    if index_expr[0] == "integer":
                        index = index_expr[1]
                        list_value = var_value[1]  
                        current_element = ("unknown", None)
                        if 0 <= index < len(list_value):
                            current_element = list_value[index]
                        if op == "=":
                            new_element_value = expr_value
                        else:
                            if current_element[0] not in ["integer", "point", "text"]:
                                self.errors.append(SemanticError(
                                    f"Operator '{op}' not applicable to element of type '{current_element[0]}'", 
                                    assign_op_node.line if hasattr(assign_op_node, 'line') else 0,
                                    assign_op_node.column if hasattr(assign_op_node, 'column') else 0))
                                return
                            if op == "+=":
                                new_element_value = self.evaluate_binary("+", current_element, expr_value)
                            elif op == "-=":
                                new_element_value = self.evaluate_binary("-", current_element, expr_value)
                            elif op == "*=":
                                new_element_value = self.evaluate_binary("*", current_element, expr_value)
                            elif op == "/=":
                                new_element_value = self.evaluate_binary("/", current_element, expr_value)
                            else:
                                new_element_value = expr_value  
                        while len(list_value) <= index:
                            list_value.append(("unknown", None))
                        list_value[index] = new_element_value
                        scope.variables[name].value = ("list", list_value)
                        print(f"List element at index {index} reassigned to {new_element_value[1]} {new_element_value[0]}")
                elif var_type == "group":
                    key_expr_node = accessor_node.children[1]
                    key_expr = self.get_value(key_expr_node)
                    if key_expr[0] not in ["text", "integer", "state", "point"]:
                        line = getattr(key_expr_node, 'line', 0)
                        column = getattr(key_expr_node, 'column', 0)
                        self.errors.append(SemanticError(
                            f"Group key must be text, integer, or state, got {key_expr[0]}", 
                            line, column))
                        return
                    group_members = var_value[1]  
                    found = False
                    member_index = -1
                    for i, (k, v) in enumerate(group_members):
                        if k[0] == key_expr[0] and k[1] == key_expr[1]:
                            found = True
                            member_index = i
                            break
                    if not found:
                        if op == "=":
                            group_members.append((key_expr, expr_value))
                            scope.variables[name].value =("group", group_members)
                            key_display = f'"{key_expr[1]}"' if key_expr[0] == "text" else str(key_expr[1])
                            print(f"Group member with key {key_display} added with value {expr_value[1]} {expr_value[0]}")
                        else:
                            line = getattr(key_expr_node, 'line', 0)
                            column = getattr(key_expr_node, 'column', 0)
                            self.errors.append(SemanticError(
                                f"Key '{key_expr[1]}' not found in group '{name}'", 
                                line, column))
                    else:
                        current_value = group_members[member_index][1]
                        if op == "=":
                            new_value = expr_value
                        else:
                            if current_value[0] not in ["integer", "point", "text"]:
                                self.errors.append(SemanticError(
                                    f"Operator '{op}' not applicable to element of type '{current_value[0]}'", 
                                    assign_op_node.line if hasattr(assign_op_node, 'line') else 0,
                                    assign_op_node.column if hasattr(assign_op_node, 'column') else 0))
                                return
                            if op == "+=":
                                new_value = self.evaluate_binary("+", current_value, expr_value)
                            elif op == "-=":
                                new_value = self.evaluate_binary("-", current_value, expr_value)
                            elif op == "*=":
                                new_value = self.evaluate_binary("*", current_value, expr_value)
                            elif op == "/=":
                                new_value = self.evaluate_binary("/", current_value, expr_value)
                            else:
                                new_value = expr_value  
                        group_members[member_index] = (key_expr, new_value)
                        scope.variables[name].value =("group", group_members)
                        key_display = f'"{key_expr[1]}"' if key_expr[0] == "text" else str(key_expr[1])
                        print(f"Group member with key {key_display} reassigned to {new_value[1]} {new_value[0]}")
        return
    def visit_id_usage(self, node):
        children = node.children
        ident = children[0]
        line = ident.line
        column = ident.column
        name = ident.value
        
        # Check if this is a function call (has func_call child)
        has_func_call = len(children) > 1 and hasattr(children[1], 'data') and children[1].data == "func_call"
        
        # Check if this is a built-in function name
        is_builtin = name in self.builtin_functions
        
        # If it's a built-in function name but NOT used with parentheses, report specific error
        if is_builtin and not has_func_call:
            self.errors.append(BuiltinFunctionWithoutParensError(name, line, column))
            result = ("unknown", None)
            self.values[id(node)] = result
            return result
        
        if has_func_call:
            arg_values = self.evaluate_function_args(children[1])
            if is_builtin:
                expected = self.builtin_functions[name]['params']
                provided = len(arg_values)
                if expected == -1:
                    if not (1 <= provided <= 2):
                        self.errors.append(ParameterMismatchError(
                            name, "1 to 2", provided, line, column))
                        result = ("unknown", None)  
                    else:
                        # Validate argument types for variadic built-in functions
                        result = self.validate_builtin_function_args(name, arg_values, line, column)
                elif expected != provided:
                    self.errors.append(ParameterMismatchError(
                        name, expected, provided, line, column))
                    result = ("unknown", None)
                else:
                    # Validate argument types
                    result = self.validate_builtin_function_args(name, arg_values, line, column)
            else:
                func_symbol = self.global_scope.lookup_function(name)
                if func_symbol is None:
                    self.errors.append(FunctionNotDefinedError(name, line, column))
                    result = ("unknown", None)
                else:
                    dynamic_result = None
                    if name in self.function_throw_expressions:
                        expr_node = self.function_throw_expressions[name]
                        args_are_dynamic = any(arg[0] in ['get', 'unknown', 'parameter'] or str(arg[0]).startswith('g') for arg in arg_values)
                        if not args_are_dynamic:
                            old_scope = self.current_scope
                            self.push_scope()
                            for i, param_name in enumerate(func_symbol.params):
                                self.current_scope.define_variable(param_name, fixed=False)
                                self.current_scope.variables[param_name].value = arg_values[i]
                            dynamic_result = self.get_value(expr_node)
                            self.pop_scope()
                            print(f"Function call '{name}' dynamically evaluated throw expression -> type {dynamic_result[0]}")
                        else:
                            print(f"Function call '{name}' has dynamic args, skipping dynamic evaluation.")
                    if dynamic_result is not None:
                        result = dynamic_result
                    else:
                        result = self.function_returns.get(name, ("empty", None))
                        print(f"Function call '{name}' using statically determined return type: {result[0]}")
                    if isinstance(result, tuple) and len(result) >= 2:
                        print(f"Function call to '{name}' result: value={result[1]}, type={result[0]}")
                    else:
                        print(f"Function call to '{name}' result: {result}")
        else:
            symbol = self.current_scope.lookup_variable(name)
            if symbol is None:
                self.errors.append(UndefinedIdentifierError(name, line, column))
                result = ("unknown", None)
            else:
                result = getattr(symbol, "value", ("empty", None))
            for child in children[1:]:
                if hasattr(child, "data"):
                    if child.data == "id_usagetail":
                        for subchild in child.children:
                            if hasattr(subchild, "data") and subchild.data == "group_or_list" and subchild.children:
                                subchild.parent = node  
                                access_result = self.visit(subchild)
                                if access_result is not None:
                                    result = access_result
                    elif child.data == "group_or_list" and child.children:
                        child.parent = node
                        access_result = self.visit(child)
                        if access_result is not None:
                            result = access_result
        self.values[id(node)] = result
        return result

    def validate_builtin_function_args(self, func_name, arg_values, line, column):
        """
        Validates the arguments provided to a built-in function.
        Returns the expected return type as (type_name, None).
        For some functions, the return type depends on the arguments.
        
        Important: Be permissive with semantic checking for edge cases - 
        trust the runtime to handle errors that can't be definitely 
        determined at compile time.
        """
        result_type = self.builtin_functions[func_name]['return_type']
        
        # Handle empty argument list
        if not arg_values:
            return (result_type, None)
        
        # Skip detailed validation for dynamic values
        if any(arg[0] in ['get', 'unknown', 'parameter'] or str(arg[0]).startswith('g') for arg in arg_values):
            print(f"Skipping detailed validation for '{func_name}' due to dynamic arguments")
            return (result_type, None)
        
        print(f"Validating arguments for built-in function '{func_name}': {arg_values}")
        
        # Specific validations based on function name
        if func_name == "length":
            if arg_values[0][0] not in ["list", "text"]:
                # Type warning but continue - runtime might handle non-list/text values
                print(f"Warning: length() expects list or text but got {arg_values[0][0]}")
        
        elif func_name in ["uppercase", "lowercase"]:
            # Very permissive - any type can be converted to string
            pass
        
        elif func_name in ["max", "min"]:
            if arg_values[0][0] not in ["list", "text", "integer", "point"]:
                # Warning only
                print(f"Warning: {func_name}() expects list, text, integer, or point but got {arg_values[0][0]}")
            
            # Determine return type based on argument type
            if arg_values[0][0] == "list" and arg_values[0][1]:
                # If the list isn't empty and has elements, infer the type from the first element
                list_vals = arg_values[0][1]
                if list_vals and isinstance(list_vals, list) and list_vals:
                    if all(isinstance(item, tuple) and len(item) >= 1 and item[0] == "integer" for item in list_vals):
                        result_type = "integer"
                    elif all(isinstance(item, tuple) and len(item) >= 1 and 
                            (item[0] == "integer" or item[0] == "point") for item in list_vals):
                        result_type = "point"
                    elif all(isinstance(item, tuple) and len(item) >= 1 and item[0] == "text" for item in list_vals):
                        result_type = "text"
            elif arg_values[0][0] == "text":
                result_type = "text"
            elif arg_values[0][0] == "integer":
                result_type = "integer"
            elif arg_values[0][0] == "point":
                result_type = "point"
        
        elif func_name == "sorted":
            if arg_values[0][0] not in ["list", "text"]:
                # Warning only
                print(f"Warning: sorted() expects list or text but got {arg_values[0][0]}")
            if len(arg_values) > 1 and arg_values[1][0] not in ["state", "integer"]:
                # Be permissive with the second argument
                print(f"Warning: second argument of sorted() should be a boolean state but got {arg_values[1][0]}")
        
        elif func_name == "reverse":
            if arg_values[0][0] not in ["list", "text"]:
                # Warning only
                print(f"Warning: reverse() expects list or text but got {arg_values[0][0]}")
            # For reverse, we can be specific about the return type
            if arg_values[0][0] == "list":
                result_type = "list"
            elif arg_values[0][0] == "text":
                result_type = "text"
        
        elif func_name == "abs":
            if arg_values[0][0] not in ["integer", "point"]:
                # Warning only
                print(f"Warning: abs() expects integer or point but got {arg_values[0][0]}")
            # Return the same type as input
            if arg_values[0][0] == "integer":
                result_type = "integer"
            elif arg_values[0][0] == "point":
                result_type = "point"
        
        elif func_name == "sum":
            if arg_values[0][0] not in ["list", "integer", "point"]:
                # Warning only
                print(f"Warning: sum() expects list, integer, or point but got {arg_values[0][0]}")
            
            # Determine return type based on argument type
            if arg_values[0][0] == "point":
                result_type = "point"
            elif arg_values[0][0] == "list":
                # Check if list contains any floats
                list_vals = arg_values[0][1]
                if list_vals and isinstance(list_vals, list):
                    if any(isinstance(item, tuple) and len(item) >= 1 and item[0] == "point" for item in list_vals):
                        result_type = "point"
                    else:
                        result_type = "integer"
            elif arg_values[0][0] == "integer":
                result_type = "integer"
        
        elif func_name == "contains":
            if len(arg_values) < 2:
                return (result_type, None)
            if arg_values[0][0] not in ["list", "text"]:
                # Warning only
                print(f"Warning: contains() first argument expects list or text but got {arg_values[0][0]}")
        
        elif func_name == "join":
            if len(arg_values) < 2:
                return (result_type, None)
            # First arg is converted to string, so no check needed
            if arg_values[1][0] != "list":
                # Warning only
                print(f"Warning: join() second argument expects list but got {arg_values[1][0]}")
        
        elif func_name == "slice":
            if len(arg_values) < 3:
                return (result_type, None)
            if arg_values[0][0] not in ["list", "text"]:
                # Warning only
                print(f"Warning: slice() first argument expects list or text but got {arg_values[0][0]}")
            if arg_values[1][0] != "integer":
                # Warning only
                print(f"Warning: slice() second argument (start index) should be an integer but got {arg_values[1][0]}")
            if arg_values[2][0] != "integer":
                # Warning only
                print(f"Warning: slice() third argument (end index) should be an integer but got {arg_values[2][0]}")
        
            # The result type is the same as the input collection type
            if arg_values[0][0] == "list":
                result_type = "list"
            elif arg_values[0][0] == "text":
                result_type = "text"
        
        elif func_name == "unique":
            if arg_values[0][0] not in ["list", "text"]:
                # Warning only
                print(f"Warning: unique() expects list or text but got {arg_values[0][0]}")
        
        elif func_name == "isqrt":
            if arg_values[0][0] not in ["integer", "point"]:
                # Warning only
                print(f"Warning: isqrt() expects integer or point but got {arg_values[0][0]}")
            
            # Only warn about negative values at compile time if they're constants
            if arg_values[0][0] == "integer" and arg_values[0][1] is not None and arg_values[0][1] < 0:
                print(f"Warning: isqrt() with negative number {arg_values[0][1]} may cause runtime error")
        
        elif func_name == "pow":
            if len(arg_values) < 2:
                return (result_type, None)
            if arg_values[0][0] not in ["integer", "point"]:
                # Warning only
                print(f"Warning: pow() first argument (base) should be a number but got {arg_values[0][0]}")
            if arg_values[1][0] not in ["integer", "point"]:
                # Warning only
                print(f"Warning: pow() second argument (exponent) should be a number but got {arg_values[1][0]}")
        
            # Determine the return type:
            # If either argument is a point, the result is a point
            if arg_values[0][0] == "point" or arg_values[1][0] == "point":
                result_type = "point"
            else:
                # If exponent is negative, result is point
                if arg_values[1][1] is not None and arg_values[1][1] < 0:
                    result_type = "point"
                else:
                    result_type = "integer"
        
        elif func_name == "factorial":
            if arg_values[0][0] not in ["integer", "point"]:
                # Warning only
                print(f"Warning: factorial() expects integer or point but got {arg_values[0][0]}")
            
            # Check for obvious issues with constants, but be permissive
            if arg_values[0][1] is not None:
                if arg_values[0][0] == "point" and not isinstance(arg_values[0][1], int) and not arg_values[0][1].is_integer():
                    print(f"Warning: factorial() with non-integer {arg_values[0][1]} may cause runtime error")
                if (arg_values[0][0] == "integer" and arg_values[0][1] < 0) or (arg_values[0][0] == "point" and arg_values[0][1] < 0):
                    print(f"Warning: factorial() with negative number {arg_values[0][1]} may cause runtime error")
                if (arg_values[0][0] == "integer" and arg_values[0][1] > 20) or (arg_values[0][0] == "point" and arg_values[0][1] > 20):
                    print(f"Warning: factorial() with large number {arg_values[0][1]} may cause overflow at runtime")
        
        elif func_name in ["ceil", "floor"]:
            if arg_values[0][0] not in ["integer", "point"]:
                # Warning only
                print(f"Warning: {func_name}() expects integer or point but got {arg_values[0][0]}")
        
        elif func_name == "round":
            if arg_values[0][0] not in ["integer", "point"]:
                # Warning only
                print(f"Warning: round() first argument expects integer or point but got {arg_values[0][0]}")
            if len(arg_values) > 1 and arg_values[1][0] != "integer":
                # Warning only
                print(f"Warning: round() second argument (decimal places) should be an integer but got {arg_values[1][0]}")
        
            # Determine return type: 
            # If decimal places is 0 or not specified, result is integer
            # Otherwise, it's a point
            if len(arg_values) == 1 or (arg_values[1][1] is not None and arg_values[1][1] == 0):
                result_type = "integer"
            else:
                result_type = "point"
        
        elif func_name == "type":
            # Always returns text
            result_type = "text"
        
        print(f"Validation of '{func_name}' complete, returning type: {result_type}")
        return (result_type, None)
    def visit_func_call(self, node):
        """
        Processes a function call.
        For semantic analysis we simply evaluate the arguments.
        """
        if len(node.children) > 1:
            args_node = node.children[1]
            args = []
            if hasattr(args_node, 'data') and args_node.data == 'args':
                for child in args_node.children:
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
        MODIFIED: Analyzes function body to determine return type.
        """
        func_token = node.children[1]
        func_name = func_token.value
        line = func_token.line
        column = func_token.column
        if func_name in self.builtin_functions:
            self.errors.append(FunctionRedefinedError(
                f"{func_name} (built-in function)", line, column))
            return
        params = []
        params_node = node.children[3]
        if hasattr(params_node, "children"):
            for child in params_node.children:
                if hasattr(child, "type") and child.type == "IDENTIFIER":
                    if child.value in params:
                        self.errors.append(SemanticError(
                            f"Parameter '{child.value}' is declared more than once in function '{func_name}'", child.line, child.column))
                    else:
                        params.append(child.value)
        elif hasattr(params_node, "type") and params_node.type == "IDENTIFIER":
            params.append(params_node.value)
        if not self.global_scope.define_function(func_name, params=params, line=line, column=column):
            self.errors.append(FunctionRedefinedError(func_name, line, column))
        print(f'Analyzing function "{func_name}" defined with parameters {params}')
        outer_function = self.current_function
        outer_has_return = self.has_return
        self.current_function = func_name
        self.has_return = False 
        self.function_returns[func_name] = ("empty", None) 
        self.function_throw_expressions.pop(func_name, None) 
        
        # Create a new scope for the function
        function_scope = self.push_scope()
        
        # Store the function scope for parameter tracking
        if func_name not in self.function_scopes:
            self.function_scopes[func_name] = []
        if function_scope not in self.function_scopes[func_name]:
            self.function_scopes[func_name].append(function_scope)
            
        # Define parameters in the function's scope
        for param_name in params:
            self.current_scope.define_variable(param_name, fixed=False, line=line, column=column)
            self.current_scope.variables[param_name].value = ("parameter", None)
            self.current_scope.variables[param_name].is_parameter = True
            
        function_body = node.children[6]
        self.visit(function_body)
        self.pop_scope()
        
        if not self.has_return:
            print(f"Function '{func_name}' has no throw statement. Assumed to return empty.")
            self.function_returns[func_name] = ("empty", None)
        elif func_name in self.function_returns:
             return_type_info = self.function_returns[func_name]
             print(f"Function '{func_name}' analysis complete. Determined return type: {return_type_info[0]}")
        else:
             print(f"Function '{func_name}' analysis complete. Throw found but type unclear, defaulting to unknown.")
             self.function_returns[func_name] = ("unknown", None)
        self.current_function = outer_function
        self.has_return = outer_has_return
        return
    def visit_function_prog(self, node):
        """
        Visits the function body (a block of statements inside the function).
        MODIFIED: Performs semantic checking on function bodies.
        """
        for child in node.children:
            self.visit(child)
        return None 
    def visit_throw_statement(self, node):
        """
        Processes a throw statement - needs to be in a function.
        MODIFIED: Evaluates the expression type and stores it and the node.
        """
        if not self.current_function:
            throw_token = node.children[0]
            line = throw_token.line
            column = throw_token.column
            self.errors.append(ControlFlowError(
                "throw", "functions", line, column))
            return None
        expr_node = node.children[1]
        thrown_value = self.get_value(expr_node)
        self.function_returns[self.current_function] = thrown_value
        self.function_throw_expressions[self.current_function] = expr_node
        self.has_return = True
        print(f"Function '{self.current_function}' throws expression. Inferred type: {thrown_value[0]}")
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
                    if hasattr(child, 'type') and child.type == "COMMA":
                        continue
                    arg_val = self.get_value(child)
                    if arg_val is not None:
                        args.append(arg_val)
            elif hasattr(args_node, 'data') or hasattr(args_node, 'type'):
                arg_val = self.get_value(args_node)
                if arg_val is not None:
                    args.append(arg_val)
        return args
    def visit_show_statement(self, node):
        """
        Semantic analysis for show_statement.
        Syntax: SHOW LPAREN expression RPAREN
        """
        expr = node.children[2]
        expr_value = self.get_value(expr)
        return None
    def visit_control_flow(self, node):
        """
        Semantic analysis for control flow statements (EXIT, NEXT).
        These should only be used inside loops.
        """
        stmt_token = node.children[0]
        stmt_type = stmt_token.value.lower()  
        line = stmt_token.line
        column = stmt_token.column
        if not self.in_loop_block:
            self.errors.append(ControlFlowError(
                stmt_type, "loops", line, column))
        return None
    def visit_variable_value(self, node):
        """
        Visit a variable_value node, which can be a list, an expression, or a GET operation.
        Enhanced to properly handle empty lists.
        """
        children = node.children
        if children and hasattr(children[0], "type") and children[0].type == "GET":
            if len(children) >= 3:
                prompt_expr = self.get_value(children[2])
                result = ("get", prompt_expr)
                self.values[id(node)] = result
                return result
        if (len(children) >= 2 and 
            hasattr(children[0], "type") and children[0].type == "LSQB" and
            hasattr(children[1], "type") and children[1].type == "RSQB"):
            result = ("list", [])
            self.values[id(node)] = result
            return result
        if not children:
            result = ("empty", None)
        elif hasattr(children[0], "type") and children[0].type == "LSQB":
            result = self.get_value(children[1])
        else:
            result = self.get_value(children[0])
        self.values[id(node)] = result
        return result
    def visit_get_operand(self, node):
        """
        Visit a get_operand node, which is the prompt inside a get() call.
        """
        if not node.children:
            return ("text", "Enter a value")
        return self.get_value(node.children[0])
    def handle_get_declaration(self, name, prompt):
        """
        Helper method to handle a variable declaration with a get() operation.
        """
        prompt_text = "Enter a value"  
        if isinstance(prompt, tuple) and len(prompt) >= 2:
            prompt_type, prompt_value = prompt
            if prompt_type == "text" and isinstance(prompt_value, str):
                prompt_text = prompt_value
            elif prompt_value is not None:
                prompt_text = str(prompt_value)
        if self.current_function:
            print(f"Declared variable {name} with get input and prompt \"{prompt_text}\" inside function {self.current_function}")
        else:
            print(f"Declared global variable {name} with get input and prompt \"{prompt_text}\"")
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
    def enter_match(self):
        """Enter a match statement context."""
        self.match_depth += 1
    def exit_match(self):
        """Exit a match statement context."""
        self.match_depth -= 1
    def check_boolean_expr(self, expr_node, context):
        """
        Check if an expression node can be evaluated as a boolean (state).
        Used for conditional statements. Allow user input in conditions.
        """
        expr_value = self.get_value(expr_node)
        if not expr_value:
            return
        allowed_types = ["state", "integer", "point", "text", "get", "unknown", "parameter"]
        if expr_value[0] not in allowed_types and not str(expr_value[0]).startswith("g"):
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
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[2])  
        condition_expr = node.children[3]
        self.check_boolean_expr(condition_expr, "each loop condition")
        self.visit(condition_expr)
        self.visit(node.children[5])  
        self.visit(node.children[7])  
        self.exit_loop()
        self.pop_scope()
        return None
    def visit_repeat_statement(self, node):
        """
        Semantic analysis for repeat_statement (while loop).
        Syntax: REPEAT LPAREN expression RPAREN LBRACE loop_block RBRACE
        """
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "repeat loop condition")
        self.visit(condition_expr)
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[4])  
        self.exit_loop()
        self.pop_scope()
        return None
    def visit_do_repeat_statement(self, node):
        """
        Semantic analysis for do_repeat_statement.
        Syntax: DO LBRACE loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[2])
        condition_expr = node.children[6]
        self.check_boolean_expr(condition_expr, "do-repeat loop condition")
        self.visit(condition_expr)
        self.exit_loop()
        self.pop_scope()
        return None
    def visit_checkif_statement(self, node):
        """
        Semantic analysis for checkif_statement (if statement).
        Syntax: CHECKIF LPAREN expression RPAREN LBRACE program RBRACE recheck_statement otherwise_statement
        """
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "checkif condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(node.children[5])
        self.pop_scope()
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
        if len(children) < 7:
            return None
        condition_expr = children[2]
        self.check_boolean_expr(condition_expr, "recheck condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(children[5])
        self.pop_scope()
        if len(children) > 7 and children[7]:
            self.visit(children[7])
        return None
    def visit_otherwise_statement(self, node):
        """
        Semantic analysis for otherwise_statement (else).
        Syntax: OTHERWISE LBRACE program RBRACE
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        self.push_scope()
        self.visit(node.children[2])
        self.pop_scope()
        return None
    def visit_match_statement(self, node):
        """
        Semantic analysis for match_statement.
        Syntax: match LPAREN expression RPAREN LBRACE CASE literals COLON program case_tail default RBRACE
        """
        self.visit(node.children[2])
        self.push_scope()
        self.enter_match()
        case_values = set()
        case_value = self.get_value(node.children[6])
        if case_value and case_value[0] != "unknown":
            case_values.add(str(case_value))
        self.visit(node.children[8])
        if len(node.children) > 9 and node.children[9]:
            self.visit_case_values(node.children[9], case_values)
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])
        self.exit_match()
        self.pop_scope()
        return None
    def visit_case_values(self, case_tail_node, case_values):
        if not case_tail_node or not hasattr(case_tail_node, 'children'):
            return
        if len(case_tail_node.children) < 2:
            return
        case_value = self.get_value(case_tail_node.children[1])
        if case_value and case_value[0] != "unknown":
            str_val = str(case_value)
            if str_val in case_values:
                line, column = 0, 0
                literal_token = case_tail_node.children[1]
                if hasattr(literal_token, 'line'):
                    line = literal_token.line
                    column = literal_token.column
                self.errors.append(SemanticError(
                    f"Duplicate case value: {case_value[1]}", line, column))
            else:
                case_values.add(str_val)
        if len(case_tail_node.children) >= 4:
            self.visit(case_tail_node.children[3])
        if len(case_tail_node.children) > 4 and case_tail_node.children[4]:
            self.visit_case_values(case_tail_node.children[4], case_values)
    def visit_group_or_list(self, node):
        if not node.children:
            return None
        is_list_access = node.children[0].type == "LSQB"
        index_expr = node.children[1]
        key_value = self.get_value(index_expr)
        parent = getattr(node, 'parent', None)
        result = ("unknown", None) 
        if parent and hasattr(parent, 'data') and parent.data == 'id_usage':
            var_name = parent.children[0].value
            var_symbol = self.current_scope.lookup_variable(var_name)
            if var_symbol:
                var_value = getattr(var_symbol, "value", None)
                if var_value:
                    var_type = var_value[0] if isinstance(var_value, tuple) else None
                    line = getattr(index_expr, 'line', 0) 
                    column = getattr(index_expr, 'column', 0) 
                    parent_line = parent.children[0].line
                    parent_column = parent.children[0].column
                    if var_type in ["parameter", "get", "unknown"] or str(var_type).startswith("g"):
                        if is_list_access:
                            print(f"Permitting list access on '{var_name}' (type {var_type}) - result type unknown.")
                            result = ("unknown", None)
                        else: 
                            print(f"Permitting group access on '{var_name}' (type {var_type}) - result type unknown.")
                            result = ("unknown", None)
                    elif is_list_access:
                        if var_type == "text":
                            text_value = var_value[1]
                            if key_value[0] == "integer":
                                idx = key_value[1]
                                if idx < 0: idx = len(text_value) + idx 
                                if 0 <= idx < len(text_value):
                                    result = ("text", text_value[idx])
                                else:
                                    self.errors.append(SemanticError(
                                        f"Text index {key_value[1]} out of range for variable '{var_name}' (length {len(text_value)})",
                                        line, column))
                                    result = ("unknown", None)
                            else:
                                 self.errors.append(SemanticError(
                                     f"Text index for '{var_name}' must be an integer, got {key_value[0]}",
                                     line, column))
                                 result = ("unknown", None)
                        elif var_type == "list":
                            list_items = var_value[1] if var_value and len(var_value) > 1 else None
                            if key_value[0] == "integer":
                                idx = key_value[1]
                                if idx is None:
                                    print(f"Warning: list index for '{var_name}' is None, treating as runtime value")
                                    result = ("unknown", None)
                                elif list_items is None:
                                    print(f"Warning: list '{var_name}' is None or not initialized, treating as runtime value")
                                    result = ("unknown", None)
                                elif 0 <= idx < len(list_items):
                                    result = list_items[idx]
                                else:
                                    print(f"Permitting potential runtime list access to '{var_name}[{idx}]'")
                                    result = ("unknown", None)
                            else:
                                self.errors.append(SemanticError(
                                    f"List index for '{var_name}' must be an integer, got {key_value[0]}",
                                    line, column))
                                result = ("unknown", None)
                        else: 
                            self.errors.append(InvalidListAccessError(
                                var_name, parent_line, parent_column))
                            result = ("unknown", None)
                    else:  
                        if var_type == "group":
                            group_members = var_value[1]  
                            found = False
                            for k, v in group_members:
                                if k[0] == key_value[0] and k[1] == key_value[1]:
                                    result = v
                                    found = True
                                    break
                            if not found:
                                self.errors.append(SemanticError(
                                    f"Key '{key_value[1]}' not found in group '{var_name}'",
                                    line, column))
                                result = ("unknown", None)
                        else: 
                            self.errors.append(InvalidGroupAccessError(
                                var_name, parent_line, parent_column))
                            result = ("unknown", None)
        self.values[id(node)] = result
        return result
    def visit_group_declaration(self, node):
        ident = node.children[1]
        line = ident.line
        column = ident.column
        name = ident.value
        if not self.current_scope.define_variable(name, fixed=False, line=line, column=column):
            self.errors.append(RedeclarationError(name, line, column))
            return
        group_data = {}
        group_members = []
        self.visit_group_members(node.children[3], group_data, group_members)
        self.current_scope.variables[name].value = ("group", group_members)
        print(f"Declared group {name} with {len(group_members)} members:")
        for key, value in group_members:
            print(f"{key[1]} ({key[0]}) : {value[1]} ({value[0]})")
        return
    def visit_group_members(self, node, group_data, group_members):
        if not node or not hasattr(node, 'children'):
            return
        key_expr = node.children[0]
        value_expr = node.children[2]
        key = self.get_value(key_expr)
        value = self.get_value(value_expr)
        if key[0] not in ["text", "integer", "state", "point"]:
            self.errors.append(SemanticError(
                f"Group key must be text, integer, or state, got {key[0]}",
                getattr(key_expr, 'line', 0), getattr(key_expr, 'column', 0)))
        else:
            str_key = str(key[1])
            if str_key in group_data:
                self.errors.append(SemanticError(
                    f"Duplicate key '{str_key}' in group",
                    getattr(key_expr, 'line', 0), getattr(key_expr, 'column', 0)))
            else:
                group_data[str_key] = True
                group_members.append((key, value))
        if len(node.children) > 3 and node.children[3]:
            self.visit_member_tail(node.children[3], group_data, group_members)
        return
    def visit_member_tail(self, node, group_data, group_members):
        if not node or not hasattr(node, 'children') or len(node.children) < 2:
            return
        self.visit_group_members(node.children[1], group_data, group_members)
        return
    def visit_start(self, node):
        for child in node.children:
            self.visit(child)
        return None
    def visit_program(self, node):
        for child in node.children:
            self.visit(child)
        return None
    def visit_loop_block(self, node):
        for child in node.children:
            self.visit(child)
        return None
    def visit_each_func_statement(self, node):
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[2])  
        condition_expr = node.children[3]
        self.check_boolean_expr(condition_expr, "each loop condition")
        self.visit(condition_expr)
        self.visit(node.children[5])  
        self.visit(node.children[7])  
        self.exit_loop()
        self.pop_scope()
        return None
    def visit_loop_func_statement(self, node):
        """
        Semantic analysis for any kind of loop inside a function.
        """
        if hasattr(node, 'data'):
            if node.data == 'each_func_statement':
                return self.visit_each_func_statement(node)
            elif node.data == 'repeat_func_statement':
                return self.visit_repeat_func_statement(node)
            elif node.data == 'do_repeat_func_statement':
                return self.visit_do_repeat_func_statement(node)
        return None
    def visit_repeat_func_statement(self, node):
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "repeat loop condition")
        self.visit(condition_expr)
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[4]) 
        self.exit_loop()
        self.pop_scope()
        return None
    def visit_do_repeat_func_statement(self, node):
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[2]) 
        condition_expr = node.children[6]
        self.check_boolean_expr(condition_expr, "do-repeat loop condition")
        self.visit(condition_expr)
        self.exit_loop()
        self.pop_scope()
        return None
    def visit_func_loop_block(self, node):
        for child in node.children:
            self.visit(child)
        return None
    def visit_func_checkif_statement(self, node):
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "checkif condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(node.children[5]) 
        self.pop_scope()
        for child in node.children[6:]:
             if child and hasattr(child, 'data'):
                 self.visit(child)
        return None
    def visit_func_recheck_statement(self, node):
        if len(node.children) < 7: return None
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "recheck condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(node.children[5]) 
        self.pop_scope()
        if len(node.children) > 7 and node.children[7]:
            self.visit(node.children[7])
        return None
    def visit_func_otherwise_statement(self, node):
        if len(node.children) < 3: return None
        self.push_scope()
        self.visit(node.children[2]) 
        self.pop_scope()
        return None
    def visit_func_match_statement(self, node):
        self.visit(node.children[2]) 
        self.push_scope()
        self.enter_match()
        case_values = set()
        case_value = self.get_value(node.children[6])
        if case_value and case_value[0] != "unknown": case_values.add(str(case_value))
        self.visit(node.children[8]) 
        if len(node.children) > 9 and node.children[9]: self.visit_func_case_tail(node.children[9], case_values)
        if len(node.children) > 10 and node.children[10]: self.visit(node.children[10]) 
        self.exit_match()
        self.pop_scope()
        return None
    def visit_func_case_tail(self, node, case_values):
        if not node or not hasattr(node, 'children') or len(node.children) < 2: return
        case_value = self.get_value(node.children[1])
        if case_value and case_value[0] != "unknown":
            str_val = str(case_value)
            if str_val in case_values:
                 line, column = getattr(node.children[1], 'line', 0), getattr(node.children[1], 'column', 0)
                 self.errors.append(SemanticError(f"Duplicate case value: {case_value[1]}", line, column))
            else: case_values.add(str_val)
        if len(node.children) >= 4: self.visit(node.children[3]) 
        if len(node.children) > 4 and node.children[4]: self.visit_func_case_tail(node.children[4], case_values)
        return
    def visit_func_loop_checkif_statement(self, node):
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "checkif condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(node.children[5]) 
        self.pop_scope()
        for child in node.children[6:]:
             if child and hasattr(child, 'data'):
                 self.visit(child)
        return None
    def visit_func_loop_recheck_statement(self, node):
        if not node or not hasattr(node, 'children') or len(node.children) < 7:
            return None
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "recheck condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(node.children[5])  
        self.pop_scope()
        if len(node.children) > 7 and node.children[7]:
            self.visit(node.children[7])
        return None
    def visit_func_loop_otherwise_statement(self, node):
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        self.push_scope()
        self.visit(node.children[2])  
        self.pop_scope()
        return None
    def visit_func_loop_match_statement(self, node):
        self.visit(node.children[2])  
        self.push_scope()
        self.enter_match()
        case_values = set()
        case_value = self.get_value(node.children[6])
        if case_value and case_value[0] != "unknown":
            case_values.add(str(case_value))
        self.visit(node.children[8])  
        if len(node.children) > 9 and node.children[9]:
            self.visit_case_tail_loop(node.children[9], case_values)
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])  
        self.exit_match()
        self.pop_scope()
        return None
    def visit_case_tail_loop(self, node, case_values):
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
        self.visit(node.children[3])  
        if len(node.children) > 4 and node.children[4]:
            self.visit_case_tail_loop(node.children[4], case_values)
        return
    def visit_func_checkif_statement(self, node):
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "checkif condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(node.children[5]) 
        self.pop_scope()
        for child in node.children[6:]:
             if child and hasattr(child, 'data'):
                 self.visit(child)
        return None
    def visit_func_recheck_statement(self, node):
        if len(node.children) < 7: return None
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "recheck condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(node.children[5]) 
        self.pop_scope()
        if len(node.children) > 7 and node.children[7]:
            self.visit(node.children[7])
        return None
    def visit_func_otherwise_statement(self, node):
        if len(node.children) < 3: return None
        self.push_scope()
        self.visit(node.children[2]) 
        self.pop_scope()
        return None
    def visit_func_match_statement(self, node):
        self.visit(node.children[2]) 
        self.push_scope()
        self.enter_match()
        case_values = set()
        case_value = self.get_value(node.children[6])
        if case_value and case_value[0] != "unknown": case_values.add(str(case_value))
        self.visit(node.children[8]) 
        if len(node.children) > 9 and node.children[9]: self.visit_func_case_tail(node.children[9], case_values)
        if len(node.children) > 10 and node.children[10]: self.visit(node.children[10]) 
        self.exit_match()
        self.pop_scope()
        return None
    def visit_func_case_tail(self, node, case_values=None):
        if not node or not hasattr(node, 'children') or len(node.children) < 2: return
        case_value = self.get_value(node.children[1])
        if case_value and case_value[0] != "unknown":
            str_val = str(case_value)
            if str_val in case_values:
                 line, column = getattr(node.children[1], 'line', 0), getattr(node.children[1], 'column', 0)
                 self.errors.append(SemanticError(f"Duplicate case value: {case_value[1]}", line, column))
            else: case_values.add(str_val)
        if len(node.children) >= 4: self.visit(node.children[3]) 
        if len(node.children) > 4 and node.children[4]: self.visit_func_case_tail(node.children[4], case_values)
        return
    def visit_func_loop_checkif_statement(self, node):
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "checkif condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(node.children[5]) 
        self.pop_scope()
        for child in node.children[6:]:
             if child and hasattr(child, 'data'):
                 self.visit(child)
        return None
    def visit_func_loop_recheck_statement(self, node):
        if not node or not hasattr(node, 'children') or len(node.children) < 7:
            return None
        condition_expr = node.children[2]
        self.check_boolean_expr(condition_expr, "recheck condition")
        self.visit(condition_expr)
        self.push_scope()
        self.visit(node.children[5])  
        self.pop_scope()
        if len(node.children) > 7 and node.children[7]:
            self.visit(node.children[7])
        return None
    def visit_func_loop_otherwise_statement(self, node):
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        self.push_scope()
        self.visit(node.children[2])  
        self.pop_scope()
        return None
    def visit_func_loop_match_statement(self, node):
        self.visit(node.children[2])  
        self.push_scope()
        self.enter_match()
        case_values = set()
        case_value = self.get_value(node.children[6])
        if case_value and case_value[0] != "unknown":
            case_values.add(str(case_value))
        self.visit(node.children[8])  
        if len(node.children) > 9 and node.children[9]:
            self.visit_case_tail_loop(node.children[9], case_values)
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])  
        self.exit_match()
        self.pop_scope()
        return None
    def visit_func_loop_case_tail(self, node, case_values):
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
        self.visit(node.children[3])  
        if len(node.children) > 4 and node.children[4]:
            self.visit_case_tail_loop(node.children[4], case_values)
        return