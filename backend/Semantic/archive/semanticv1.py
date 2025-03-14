import re
from lark import Transformer
from .symbol_table import SymbolTable
from .semantic_errors import SemanticError

# Helper conversion functions for state values.
def convert_state_to_int(state):
    # YES -> 1, NO -> 0
    return 1 if state == "YES" else 0

def convert_state_to_point(state):
    # YES -> 1.0, NO -> 0.0
    return 1.0 if state == "YES" else 0.0

class SemanticAnalyzer(Transformer):
    def __init__(self):
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.errors = []  # List of SemanticError objects

    def push_scope(self):
        self.current_scope = SymbolTable(parent=self.current_scope)

    def pop_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

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
        if hasattr(node, "data"):
            if node.data == "var_init":
                if node.children and len(node.children) >= 2:
                    return self.extract_literal(node.children[1])
                else:
                    return None
            if node.data == "variable_value":
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

    def list_value(self, items):
        # 'items' contains the first expression and (optionally) the list_tail.
        result = [items[0]]
        if len(items) > 1:
            # items[1] is already a list of additional elements.
            if isinstance(items[1], list):
                result.extend(items[1])
            else:
                result.append(items[1])
        return ("list", result)

    def list_tail(self, items):
        # 'items' matches: COMMA, expression, and optionally another list_tail.
        result = []
        if len(items) >= 2:
            result.append(items[1])
        if len(items) == 3:
            # The third item is a list_tail that is already transformed to a list.
            if isinstance(items[2], list):
                result.extend(items[2])
            else:
                result.append(items[2])
        return result

    # Helper to convert a value (with its type) to a numeric value for arithmetic.
    def to_numeric(self, typ, value, target="int"):
        if typ == "state":
            return (float(convert_state_to_point(value)) if target == "point" 
                    else convert_state_to_int(value))
        elif typ == "integer":
            return value
        elif typ == "point":
            return value
        else:
            return 0

    def evaluate_binary(self, op, left, right):
        """
        Evaluate a binary arithmetic expression.
        left and right are tuples: (type, value)
        Returns a tuple (result_type, result_value)
        """
        left_type, left_val = left
        right_type, right_val = right

        # Handle text concatenation with +
        if op == "+" and (left_type == "text" or right_type == "text"):
            return ("text", str(left_val) + str(right_val)) if (left_val := left_val if 'left_val' in locals() else left_val) else None

        # Disallow non-plus operators on text.
        if left_type == "text" or right_type == "text":
            self.errors.append(SemanticError(
                f"Operator '{op}' not allowed on text type", 0, 0))
            return ("unknown", None)

        # Determine arithmetic mode.
        use_point = False
        if op == "/":
            use_point = True
        elif left_type == "point" or right_type == "point":
            use_point = True
        elif (left_type == "state" and right_type == "point") or (left_type == "point" and right_type == "state"):
            use_point = True

        L = self.to_numeric(left_type, left[1], "point" if use_point else "int")
        R = self.to_numeric(right_type, right_val, "point" if use_point else "int")  # left_val and right_val fix
        # Correction: use left_val and right_val extracted from left and right.
        left_val = self.to_numeric(left_type, left[1], "point" if use_point else "int")
        right_val = self.to_numeric(right_type, right[1], "point" if use_point else "int")

        result = None
        try:
            if op == "+":
                result = left_val + right_val
            elif op == "-":
                result = left_val - right_val
            elif op == "*":
                result = left_val * right_val
            elif op == "/":
                result = left_val / right_val
            elif op == "%":
                result = left_val % right_val
            else:
                self.errors.append(SemanticError(
                    f"Unsupported operator '{op}'", 0, 0))
                return ("unknown", None)
        except Exception as e:
            self.errors.append(SemanticError(
                f"Error evaluating expression: {str(e)}", 0, 0))
            return ("unknown", None)

        return ("point", result) if use_point else ("integer", result)

    # Updated binary evaluation to call the helper above.
    def evaluate_binary(self, op, left, right):
        # New check for list addition.
        if op == "+":
            if left[0] == "list" or right[0] == "list":
                if left[0] == "list" and right[0] == "list":
                    # Valid: concatenate lists.
                    return ("list", left[1] + right[1])
                else:
                    # Error: cannot add a list to a non-list.
                    self.errors.append(SemanticError("Operator '+' not allowed between a list and a non-list", 0, 0))
                    return ("unknown", None)
        
        # Existing text concatenation branch.
        if op == "+" and (left[0] == "text" or right[0] == "text"):
            return ("text", str(left[1]) + str(right[1]))
        
        # Disallow operators on text for non-concatenation.
        if left[0] == "text" or right[0] == "text":
            self.errors.append(SemanticError(
                f"Operator '{op}' not allowed on text type", 0, 0))
            return ("unknown", None)
        
        # Determine arithmetic mode.
        use_point = False
        if op == "/":
            use_point = True
        elif left[0] == "point" or right[0] == "point":
            use_point = True
        elif (left[0] == "state" and right[0] == "point") or (left[0] == "state" and right[0] == "state"):
            use_point = False
        
        # Convert operands to numeric.
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
                result = L / R
            elif op == "%":
                result = L % R
            else:
                self.errors.append(SemanticError(
                    f"Unsupported operator '{op}'", 0, 0))
                return ("unknown", None)
        except Exception as e:
            self.errors.append(SemanticError(
                f"Error evaluating expression: {str(e)}", 0, 0))
            return ("unknown", None)

        # Determine result type.
        if use_point:
            return ("point", result)
        else:
            return ("integer", result)

    def to_numeric(self, typ, value, target="int"):
        if typ == "state":
            return convert_state_to_point(value) if target == "point" else convert_state_to_int(value)
        elif typ == "integer":
            return value
        elif typ == "point":
            return value
        else:
            return 0

    def to_bool(self, expr):
        typ, val = expr
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
    # Transformer Methods (Expressions)
    ##############################
    def expression(self, items):
        return items[0]

    def logical_or_expr(self, items):
        result = items[0]
        i = 1
        while i < len(items):
            op = items[i].value  # "||"
            right = items[i+1]
            result_bool = self.to_bool(result) or self.to_bool(right)
            result = ("state", "YES" if result_bool else "NO")
            i += 2
        return result

    def logical_and_expr(self, items):
        result = items[0]
        i = 1
        while i < len(items):
            op = items[i].value  # "&&"
            right = items[i+1]
            result_bool = self.to_bool(result) and self.to_bool(right)
            result = ("state", "YES" if result_bool else "NO")
            i += 2
        return result

    def equality_expr(self, items):
        if len(items) == 1:
            return items[0]
        left = items[0]
        op = items[1].value  # "==" or "!="
        right = items[2]
        if op == "==":
            result = left[1] == right[1]
        else:
            result = (left[1] != right[1])
        return ("state", "YES" if result else "NO")

    def relational_expr(self, items):
        if len(items) == 1:
            return items[0]
        left = items[0]
        op = items[1].value
        right = items[2]
        if op == "<":
            result = (left[1] < right[1])
        elif op == "<=":
            result = (left[1] <= right[1])
        elif op == ">":
            result = (left[1] > right[1])
        elif op == ">=":
            result = (left[1] >= right[1])
        else:
            result = False
        return ("state", "YES" if result else "NO")

    def add_expr(self, items):
        result = items[0]
        i = 1
        while i < len(items):
            op = items[i].value  # PLUS or MINUS
            right = items[i+1]
            result = self.evaluate_binary(op, result, right)
            i += 2
        return result

    def mul_expr(self, items):
        result = items[0]
        i = 1
        while i < len(items):
            op = items[i].value  # STAR, SLASH, or PERCENT
            right = items[i+1]
            result = self.evaluate_binary(op, result, right)
            i += 2
        return result

    def pre_expr(self, items):
        if len(items) == 1:
            return items[0]
        op_token = items[0]
        expr = items[1]
        if op_token.value == "!":
            result_bool = not self.to_bool(expr)
            return ("state", "YES" if result_bool else "NO")
        elif op_token.value == "~":
            typ, val = expr
            if typ == "state":
                # Convert "YES" to -1, "NO" to 0
                return ("integer", -convert_state_to_int(val))
            return (typ, -val)

    def primary_expr(self, items):
        if len(items) == 1:
            return items[0]
        return items[1]

    def operand(self, items):
        return items[0]

    def typecast_expression(self, items):
        # items[0]: target type token; items[2]: expression result.
        target_token = items[0]
        inner = items[2]  # (type, value)
        current_type, current_value = inner
        target = target_token.value.lower()  # "integer", "point", "state", "text"
        try:
            if target == "integer":
                if current_type == "point":
                    return ("integer", int(current_value))
                elif current_type == "text":
                    return ("integer", int(current_value))  # May raise ValueError
                elif current_type == "state":
                    return ("integer", 1 if current_value == "YES" else 0)
                else:
                    return inner
            elif target == "point":
                if current_type == "integer":
                    return ("point", float(current_value))
                elif current_type == "text":
                    return ("point", float(current_value))
                elif current_type == "state":
                    return ("point", 1.0 if current_value == "YES" else 0.0)
                else:
                    return inner
            elif target == "text":
                return ("text", str(current_value))
            elif target == "state":
                if current_type in ("integer", "point"):
                    return ("state", "YES" if current_value != 0 and current_value != 0.0 else "NO")
                elif current_type == "text":
                    return ("state", "YES" if current_value != "" else "NO")
                else:
                    return inner
            else:
                return inner
        except Exception as e:
            self.errors.append(SemanticError(
                f"Error in typecasting: {str(e)}", 0, 0))
            return ("unknown", None)

    # Literals
    def TEXTLITERAL(self, token):
        return ("text", token.value.strip('"'))

    def INTEGERLITERAL(self, token):
        return ("integer", int(token.value))

    def NEGINTEGERLITERAL(self, token):
        return ("integer", -int(token.value[1:]))

    def POINTLITERAL(self, token):
        return ("point", float(token.value))

    def NEGPOINTLITERAL(self, token):
        return ("point", -float(token.value[1:]))

    def STATELITERAL(self, token):
        return ("state", token.value)

    def EMPTY(self, token):
        return ("empty", None)

    ##############################
    # Transformer Methods (Declarations, Assignments, etc.)
    ##############################

    def varlist_declaration(self, items):
        if len(items) < 2:
            return
        ident = items[1]
        line = ident.line
        column = ident.column
        name = ident.value
        
        # Always define in the current scope (local or global)
        if not self.current_scope.define_variable(name, fixed=False, line=line, column=column):
            self.errors.append(SemanticError(
                f"Variable '{name}' is already declared in this scope", line, column))
            return

        if len(items) >= 3 and items[2] and not (hasattr(items[2], "type") and items[2].type == "SEMICOLON"):
            literal_node = self.extract_literal(items[2])
            if literal_node is not None:
                expr_value = self.transform(literal_node)
                print(f"Declared variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                self.current_scope.variables[name].value = expr_value
            else:
                print(f"Declared variable {name} with empty value")
        else:
            print(f"Declared variable {name} with empty value")
        return

    def varlist_tail(self, items):
        if not items:
            return
        ident = items[1]
        line = ident.line
        column = ident.column
        name = ident.value
        if not self.current_scope.define_variable(name, fixed=False, line=line, column=column):
            self.errors.append(SemanticError(
                f"Variable '{name}' is already declared in this scope", line, column))
            return
        if len(items) > 2 and items[2]:
            literal_node = self.extract_literal(items[2])
            if literal_node is not None:
                expr_value = self.transform(literal_node)
                print(f"Declared variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                self.current_scope.variables[name].value = expr_value
            else:
                print(f"Declared variable {name} with empty value")
        else:
            print(f"Declared variable {name} with empty value")
        return

    # --- Fixed Declarations ---
    def fixed_declaration(self, items):
        ident = items[1]
        line = ident.line
        column = ident.column
        name = ident.value
        if not self.current_scope.define_variable(name, fixed=True, line=line, column=column):
            self.errors.append(SemanticError(
                f"Fixed variable '{name}' is already declared in this scope", line, column))
            return
        if len(items) > 3 and items[3]:
            literal_node = self.extract_literal(items[3])
            if literal_node is not None:
                expr_value = self.transform(literal_node)
                print(f"Declared fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                self.current_scope.variables[name].value = expr_value
            else:
                print(f"Declared fixed variable {name} with empty value")
        else:
            print(f"Declared fixed variable {name} with empty value")
        return

    def fixed_tail(self, items):
        if not items:
            return
        ident = items[1]
        line = ident.line
        column = ident.column
        name = ident.value
        if not self.current_scope.define_variable(name, fixed=True, line=line, column=column):
            self.errors.append(SemanticError(
                f"Fixed variable '{name}' is already declared in this scope", line, column))
            return
        if len(items) > 2 and items[2]:
            literal_node = self.extract_literal(items[2])
            if literal_node is not None:
                expr_value = self.transform(literal_node)
                print(f"Declared fixed variable {name} with expression value {expr_value[1]} and type {expr_value[0]}")
                self.current_scope.variables[name].value = expr_value
            else:
                print(f"Declared fixed variable {name} with empty value")
        else:
            print(f"Declared fixed variable {name} with empty value")
        return

    def var_assign(self, items):
        ident = items[0]
        line = ident.line
        column = ident.column
        name = ident.value
        symbol = self.current_scope.lookup_variable(name)
        if symbol is None:
            self.errors.append(SemanticError(
                f"Variable '{name}' is not declared", line, column))
            return
        if symbol.fixed:
            self.errors.append(SemanticError(
                f"Fixed variable '{name}' cannot be reassigned", line, column))
            return
        literal_node = self.extract_literal(items[3])
        expr_value = self.transform(literal_node)
        print(f"Variable {name} reassigned to expression value {expr_value[1]} and type {expr_value[0]}")
        self.current_scope.variables[name].value = expr_value
        return

    def func_definition(self, items):
        ident = items[1]
        line = ident.line
        column = ident.column
        func_name = ident.value
        params = items[3] if items[3] is not None else []
        
        # Define the function in the global scope
        if not self.global_scope.define_function(func_name, params=params, line=line, column=column):
            self.errors.append(SemanticError(
                f"Function '{func_name}' is already defined", line, column))
        
        # Create a new scope for the function body
        self.push_scope()
        
        # Define each parameter as a variable in the function scope
        for param in params:
            param_name = param  # already a string
            if not self.current_scope.define_variable(param_name, fixed=False, line=line, column=column):
                self.errors.append(SemanticError(
                    f"Parameter '{param_name}' is already declared in the function scope", line, column))
            else:
                # Initialize with an empty value to ensure it's recognized as declared
                self.current_scope.variables[param_name].value = ("unknown", None)
        
        # Process the function body
        self.transform(items[6])
        
        # Restore the previous scope
        self.pop_scope()
        return

    def param(self, items):
        """
        With the new grammar, items will contain IDENTIFIER tokens and literal COMMA tokens.
        We want to filter out the commas and return only the identifier values.
        """
        return [item.value for item in items if hasattr(item, "type") and item.type == "IDENTIFIER"]

    def func_call(self, items):
        args = items[1] if items[1] is not None else []
        arg_count = len(args) if isinstance(args, list) else 1
        return {"type": "func_call", "arg_count": arg_count}

    def args(self, items):
        if not items:
            return []
        args_list = [None]
        if len(items) > 1 and items[1]:
            if isinstance(items[1], list):
                args_list.extend([None] * len(items[1]))
            else:
                args_list.append(None)
        return args_list

    def args_tail(self, items):
        if not items:
            return []
        args_list = [None]
        if len(items) > 2 and items[2]:
            if isinstance(items[2], list):
                args_list.extend([None] * len(items[2]))
            else:
                args_list.append(None)
        return args_list

    def id_usage(self, items):
        ident = items[0]
        line = ident.line
        column = ident.column
        name = ident.value
        if len(items) > 1 and isinstance(items[1], dict) and items[1].get("type") == "func_call":
            func_symbol = self.global_scope.lookup_function(name)
            if func_symbol is None:
                self.errors.append(SemanticError(
                    f"Function '{name}' is not defined", line, column))
            else:
                expected = len(func_symbol.params)
                provided = items[1].get("arg_count", 0)
                if expected != provided:
                    self.errors.append(SemanticError(
                        f"Function '{name}' expects {expected} arguments, but {provided} were provided",
                        line, column))
            return ("unknown", None)
        else:
            symbol = self.current_scope.lookup_variable(name)
            if symbol is None:
                self.errors.append(SemanticError(
                    f"Variable '{name}' is not declared", line, column))
                return ("unknown", None)
            return getattr(symbol, "value", ("empty", None))

    #######################
    # Literal Evaluations
    #######################
    def TEXTLITERAL(self, token):
        return ("text", token.value.strip('"'))

    def INTEGERLITERAL(self, token):
        return ("integer", int(token.value))

    def NEGINTEGERLITERAL(self, token):
        return ("integer", -int(token.value[1:]))

    def POINTLITERAL(self, token):
        return ("point", float(token.value))

    def NEGPOINTLITERAL(self, token):
        return ("point", -float(token.value[1:]))

    def STATELITERAL(self, token):
        return ("state", token.value)

    def EMPTY(self, token):
        return ("empty", None)