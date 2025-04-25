import re
from lark import Visitor
from .Semantic.symbol_table import SymbolTable
from .Semantic.semantic_errors import (
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
def convert_state_to_int(state):
    return 1 if state == "YES" else 0
def convert_state_to_point(state):
    return 1.0 if state == "YES" else 0.0
class SemanticAndCodeGenVisitor(Visitor):
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
        self.function_returns = {}
        self.function_throw_expressions = {}
        self.loop_stack = []
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.current_scope_name = "global"
        self.scope_stack = ["global"]
        self.control_stack = []
        self.variable_types = {}
    def safe_extract_tuple_value(self, value, default_type="unknown"):
        """Safely extract type and value from potentially complex result tuples."""
        if isinstance(value, tuple):
            if len(value) >= 2:
                return value[0], value[1]
            elif len(value) == 1:
                return value[0], None
            else:
                return default_type, None
        else:
            return default_type, value
    def analyze_and_generate(self, tree):
        self.errors = []
        self.values = {}
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.variable_types = {}
        self.visit(tree)
        unique_errors = []
        error_signatures = set()
        for error in self.errors:
            signature = (error.message, error.line, error.column)
            if signature not in error_signatures:
                error_signatures.add(signature)
                unique_errors.append(error)
        self.errors = unique_errors
        return self.errors, self.instructions
    def push_scope(self):
        self.current_scope = SymbolTable(parent=self.current_scope)
    def pop_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
    def get_semantic_value(self, node):
        """Retrieves the cached semantic value (type, value) for a node."""
        node_id = id(node)
        if node_id in self.values:
            return self.values[node_id]

        if hasattr(node, 'type'):
            self.visit_token(node)
            if node_id in self.values:
                return self.values[node_id]
            else:
                return ("unknown", None)

        return ("unknown", None)
    def get_value(self, node):
        if id(node) in self.values:
            return self.values[id(node)]
        if hasattr(node, 'data'):
            result = self.visit(node)
            return result
        elif hasattr(node, 'type'):
            return self.visit_token(node)
        return None
    def get_temp(self):
        self.temp_counter += 1
        return f"t{self.temp_counter}"
    def get_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"
    def emit(self, op, arg1=None, arg2=None, result=None):
        instruction = (op, arg1, arg2, result)
        self.instructions.append(instruction)
        return instruction
    def push_loop(self, start_label, end_label):
        self.loop_stack.append((start_label, end_label))
    def pop_loop(self):
        if self.loop_stack:
            return self.loop_stack.pop()
        return None
    def get_current_loop_labels(self):
        if self.loop_stack:
            return self.loop_stack[-1]
        return None, None
    def enter_loop(self):
        self.loop_depth += 1
        self.in_loop_block = True
    def exit_loop(self):
        self.loop_depth -= 1
        if self.loop_depth == 0:
            self.in_loop_block = False
    def enter_switch(self):
        self.switch_depth += 1
    def exit_switch(self):
        self.switch_depth -= 1
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
    def visit_token(self, token):
        token_id = id(token)
        if token_id in self.values:
            semantic_val = self.values[token_id]
            type, val = semantic_val
            if type == "text": return f'"{val}"'
            if type == "state": return 1 if val == "YES" else 0
            if type == "empty": return None
            return val

        tac_ref = token.value
        result = ("unknown", token.value)

        if token.type == 'TEXTLITERAL':
            val = token.value.strip('"')
            result = ("text", val)
            tac_ref = f'"{val}"'
        elif token.type == 'INTEGERLITERAL':
            val = int(token.value)
            result = ("integer", val)
            tac_ref = val
        elif token.type == 'NEGINTEGERLITERAL':
            val_str = token.value[1:] if token.value.startswith('~') else token.value
            val = -int(val_str)
            result = ("integer", val)
            tac_ref = val
        elif token.type == 'POINTLITERAL':
            val = float(token.value)
            result = ("point", val)
            tac_ref = val
        elif token.type == 'NEGPOINTLITERAL':
            val_str = token.value[1:] if token.value.startswith('~') else token.value
            val = -float(val_str)
            result = ("point", val)
            tac_ref = val
        elif token.type == 'STATELITERAL':
            val = token.value
            result = ("state", val)
            tac_ref = 1 if val == "YES" else 0
        elif token.type == 'EMPTY':
            result = ("empty", None)
            tac_ref = None

        self.values[token_id] = result
        return tac_ref
    def infer_type_and_value(self, raw_value):
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
        if node is None:
            return None
        if hasattr(node, "data") and node.data == "expression":
            self._validate_expression_for_list_access(node)
        if hasattr(node, "data"):
            if node.data == "var_init":
                if node.children and len(node.children) >= 2:
                    return self.extract_literal(node.children[1])
                else:
                    return None
            if node.data == "variable_value":
                if node.children and hasattr(node.children[0], "type") and node.children[0].type == "GET":
                    return node
                if node.children and hasattr(node.children[0], "type") and node.children[0].type == "LSQB":
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
        if not hasattr(node, "children"):
            return
        if hasattr(node, "data") and (node.data == "id_usage" or node.data == "operand"):
            self._check_node_for_list_access(node)
        for child in node.children:
            self._validate_expression_for_list_access(child)
    def _check_node_for_list_access(self, node):
        if not hasattr(node, "children") or len(node.children) < 1:
            return
        var_name = None
        if hasattr(node, "data") and node.data == "id_usage" and hasattr(node.children[0], "value"):
            var_name = node.children[0].value
        elif hasattr(node.children[0], "data") and node.children[0].data == "id_usage":
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
        if var_type == "parameter" or var_type == "get" or var_type == "unknown":
            return
        for child in node.children:
            if (hasattr(child, "data") and child.data == "group_or_list" and 
                child.children and hasattr(child.children[0], "type")):
                if child.children[0].type == "LSQB" and var_type != "list" and var_type != "text":
                    line = node.children[0].line if hasattr(node.children[0], "line") else 0
                    column = node.children[0].column if hasattr(node.children[0], "column") else 0
                    self.errors.append(InvalidListAccessError(var_name, line, column))
                    return
                elif child.children[0].type == "LBRACE" and var_type != "group":
                    line = node.children[0].line if hasattr(node.children[0], "line") else 0
                    column = node.children[0].column if hasattr(node.children[0], "column") else 0
                    self.errors.append(InvalidGroupAccessError(var_name, line, column))
                    return
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
                if R == 0 or R == 0.0:
                     self.errors.append(SemanticError(
                         "Division by zero", line, column))
                     return ("unknown", None)
                result = L / R
            elif op == "%":
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
        result = self.get_value(node.children[0])
        self.values[id(node)] = result
        if result and isinstance(result, tuple) and len(result) > 0:
            self._check_invalid_access_in_expr(node)
        return result
    def _check_invalid_access_in_expr(self, node):
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
        if len(children) == 1:
            tac_ref = self.visit(children[0])
            self.values[id(node)] = self.get_semantic_value(children[0])
            return tac_ref

        left_ref = self.visit(children[0])
        i = 1
        current_semantic_result = self.get_semantic_value(children[0])

        while i < len(children):
            right_node = children[i+1]
            right_ref = self.visit(right_node)

            left_semantic = current_semantic_result
            right_semantic = self.get_semantic_value(right_node)
            result_bool = self.to_state(left_semantic) or self.to_state(right_semantic)
            current_semantic_result = ("state", "YES" if result_bool else "NO")

            temp = self.get_temp()
            self.emit('OR', left_ref, right_ref, temp)
            self.variable_types[temp] = "state"

            left_ref = temp
            i += 2

        self.values[id(node)] = current_semantic_result
        return left_ref
    def visit_logical_and_expr(self, node):
        children = node.children
        if len(children) == 1:
            tac_ref = self.visit(children[0])
            self.values[id(node)] = self.get_semantic_value(children[0])
            return tac_ref

        left_ref = self.visit(children[0])
        i = 1
        current_semantic_result = self.get_semantic_value(children[0])

        while i < len(children):
            right_node = children[i+1]
            right_ref = self.visit(right_node)

            left_semantic = current_semantic_result
            right_semantic = self.get_semantic_value(right_node)
            result_bool = self.to_state(left_semantic) and self.to_state(right_semantic)
            current_semantic_result = ("state", "YES" if result_bool else "NO")

            temp = self.get_temp()
            self.emit('AND', left_ref, right_ref, temp)
            self.variable_types[temp] = "state"

            left_ref = temp
            i += 2

        self.values[id(node)] = current_semantic_result
        return left_ref
    def visit_equality_expr(self, node):
        children = node.children
        if len(children) == 1:
            tac_ref = self.visit(children[0])
            self.values[id(node)] = self.get_semantic_value(children[0])
            return tac_ref

        left_node = children[0]
        op = children[1].value
        right_node = children[2]

        left_ref = self.visit(left_node)
        right_ref = self.visit(right_node)

        left_semantic = self.get_semantic_value(left_node)
        right_semantic = self.get_semantic_value(right_node)
        comparison_result = False
        try:
            l_type, l_val = self.safe_extract_tuple_value(left_semantic)
            r_type, r_val = self.safe_extract_tuple_value(right_semantic)

            is_left_empty = l_type == "empty" or l_val is None
            is_right_empty = r_type == "empty" or r_val is None

            if is_left_empty or is_right_empty:
                 comparison_result = (is_left_empty == is_right_empty) if op == "==" else (is_left_empty != is_right_empty)
            elif l_type in ["get", "unknown", "parameter"] or r_type in ["get", "unknown", "parameter"]:
                 comparison_result = False
            else:
                 comparison_result = (l_val == r_val) if op == "==" else (l_val != r_val)

            result_semantic = ("state", "YES" if comparison_result else "NO")

        except TypeError:
             line = children[1].line
             column = children[1].column
             self.errors.append(TypeMismatchError(left_semantic[0], right_semantic[0], f"equality comparison ('{op}')", line, column))
             result_semantic = ("unknown", None)
        except Exception as e:
             line = children[1].line
             column = children[1].column
             self.errors.append(SemanticError(f"Error in equality comparison: {str(e)}", line, column))
             result_semantic = ("unknown", None)

        temp = self.get_temp()
        tac_op = 'EQ' if op == "==" else 'NEQ'
        self.emit(tac_op, left_ref, right_ref, temp)
        self.variable_types[temp] = "state"

        self.values[id(node)] = result_semantic
        return temp
    def visit_relational_expr(self, node):
        children = node.children
        if len(children) == 1:
            tac_ref = self.visit(children[0])
            self.values[id(node)] = self.get_semantic_value(children[0])
            return tac_ref

        left_node = children[0]
        op = children[1].value
        right_node = children[2]

        left_ref = self.visit(left_node)
        right_ref = self.visit(right_node)

        left_semantic = self.get_semantic_value(left_node)
        right_semantic = self.get_semantic_value(right_node)
        comparison = False
        result_semantic = ("state", "NO")
        try:
            l_type, l_val = self.safe_extract_tuple_value(left_semantic)
            r_type, r_val = self.safe_extract_tuple_value(right_semantic)

            non_comparable = ["list", "group", "empty", "unknown", "get", "parameter"]
            if l_type in non_comparable or r_type in non_comparable or l_val is None or r_val is None:
                 if l_type not in non_comparable and r_type not in non_comparable:
                      line = children[1].line
                      column = children[1].column
                      self.errors.append(TypeMismatchError(l_type, r_type, f"relational comparison ('{op}')", line, column))
                 result_semantic = ("unknown", None)
            else:
                 if op == "<": comparison = l_val < r_val
                 elif op == "<=": comparison = l_val <= r_val
                 elif op == ">": comparison = l_val > r_val
                 elif op == ">=": comparison = l_val >= r_val
                 result_semantic = ("state", "YES" if comparison else "NO")

        except TypeError:
             line = children[1].line
             column = children[1].column
             self.errors.append(TypeMismatchError(left_semantic[0], right_semantic[0], f"relational comparison ('{op}')", line, column))
             result_semantic = ("unknown", None)
        except Exception as e:
             line = children[1].line
             column = children[1].column
             self.errors.append(SemanticError(f"Error in comparison: {str(e)}", line, column))
             result_semantic = ("unknown", None)

        temp = self.get_temp()
        tac_op_map = {"<": "LT", "<=": "LE", ">": "GT", ">=": "GE"}
        tac_op = tac_op_map.get(op, "ERROR")
        if tac_op != "ERROR":
            self.emit(tac_op, left_ref, right_ref, temp)
        else:
            self.emit('ERROR', f"Unsupported relational operator '{op}'", None, temp)
        self.variable_types[temp] = "state"

        self.values[id(node)] = result_semantic
        return temp
    def visit_add_expr(self, node):
        children = node.children
        if len(children) == 1:
            tac_ref = self.visit(children[0])
            self.values[id(node)] = self.get_semantic_value(children[0])
            return tac_ref

        left_ref = self.visit(children[0])
        i = 1
        current_semantic_result = self.get_semantic_value(children[0])

        while i < len(children):
            op_token = children[i]
            op = op_token.value
            right_node = children[i+1]
            right_ref = self.visit(right_node)

            left_semantic = current_semantic_result
            right_semantic = self.get_semantic_value(right_node)
            current_semantic_result = self.evaluate_binary(op, left_semantic, right_semantic, op_token.line, op_token.column)
            result_type = current_semantic_result[0]

            temp = self.get_temp()
            if op == "+":
                if result_type == "list":
                    self.emit('LIST_CONCAT', left_ref, right_ref, temp)
                    self.variable_types[temp] = "list"
                elif result_type == "text":
                    self.emit('CONCAT', left_ref, right_ref, temp)
                    self.variable_types[temp] = "text"
                elif result_type in ["integer", "point"]:
                    self.emit('ADD', left_ref, right_ref, temp)
                    self.variable_types[temp] = result_type
                else:
                    self.emit('ERROR', f"Invalid '+' operation between {left_semantic[0]} and {right_semantic[0]}", None, temp)
                    self.variable_types[temp] = "unknown"
            else:
                 if result_type in ["integer", "point"]:
                    self.emit('SUB', left_ref, right_ref, temp)
                    self.variable_types[temp] = result_type
                 else:
                    self.emit('ERROR', f"Invalid '-' operation between {left_semantic[0]} and {right_semantic[0]}", None, temp)
                    self.variable_types[temp] = "unknown"

            left_ref = temp
            i += 2

        self.values[id(node)] = current_semantic_result
        return left_ref
    def visit_mul_expr(self, node):
        children = node.children
        if len(children) == 1:
            tac_ref = self.visit(children[0])
            self.values[id(node)] = self.get_semantic_value(children[0])
            return tac_ref

        left_ref = self.visit(children[0])
        i = 1
        current_semantic_result = self.get_semantic_value(children[0])

        while i < len(children):
            op_token = children[i]
            op = op_token.value
            right_node = children[i+1]
            right_ref = self.visit(right_node)

            left_semantic = current_semantic_result
            right_semantic = self.get_semantic_value(right_node)
            current_semantic_result = self.evaluate_binary(op, left_semantic, right_semantic, op_token.line, op_token.column)
            result_type = current_semantic_result[0]

            temp = self.get_temp()
            if op == "*":
                if result_type in ["integer", "point"]:
                    self.emit('MUL', left_ref, right_ref, temp)
                    self.variable_types[temp] = result_type
                else:
                    self.emit('ERROR', f"Invalid '*' operation between {left_semantic[0]} and {right_semantic[0]}", None, temp)
                    self.variable_types[temp] = "unknown"
            elif op == "/":
                 if result_type == "point":
                    self.emit('DIV', left_ref, right_ref, temp)
                    self.variable_types[temp] = "point"
                 else:
                    self.emit('ERROR', f"Invalid '/' operation between {left_semantic[0]} and {right_semantic[0]}", None, temp)
                    self.variable_types[temp] = "unknown"
            else:
                 if result_type in ["integer", "point"]:
                    self.emit('MOD', left_ref, right_ref, temp)
                    self.variable_types[temp] = result_type
                 else:
                    self.emit('ERROR', f"Invalid '%' operation between {left_semantic[0]} and {right_semantic[0]}", None, temp)
                    self.variable_types[temp] = "unknown"

            left_ref = temp
            i += 2

        self.values[id(node)] = current_semantic_result
        return left_ref
    def visit_pre_expr(self, node):
        children = node.children
        if len(children) == 1:
            tac_ref = self.visit(children[0])
            self.values[id(node)] = self.get_semantic_value(children[0])
            return tac_ref

        op_token = children[0]
        op = op_token.value
        expr_node = children[1]

        expr_ref = self.visit(expr_node)
        expr_semantic = self.get_semantic_value(expr_node)

        result_semantic = ("unknown", None)
        if op == "!":
            result_bool = not self.to_state(expr_semantic)
            result_semantic = ("state", "YES" if result_bool else "NO")
        elif op == "~":
            typ, val = self.safe_extract_tuple_value(expr_semantic)
            negated_val = None
            result_type = "unknown"
            try:
                if typ == "state":
                    negated_val = -convert_state_to_int(val)
                    result_type = "integer"
                elif typ == "integer":
                    negated_val = -val
                    result_type = "integer"
                elif typ == "point":
                    negated_val = -val
                    result_type = "point"
                else:
                    line = op_token.line
                    column = op_token.column
                    self.errors.append(TypeMismatchError("integer, point, or state", typ, "negation ('~')", line, column))
                    result_type = "unknown"
                result_semantic = (result_type, negated_val)
            except Exception as e:
                 line = op_token.line
                 column = op_token.column
                 self.errors.append(SemanticError(f"Error during negation: {e}", line, column))
                 result_semantic = ("unknown", None)

        temp = self.get_temp()
        tac_op = 'NOT' if op == "!" else 'NEG'
        self.emit(tac_op, expr_ref, None, temp)
        self.variable_types[temp] = result_semantic[0] if result_semantic[0] != "unknown" else "integer"

        self.values[id(node)] = result_semantic
        return temp
    def visit_primary_expr(self, node):
        if len(node.children) == 1:
            child_node = node.children[0]
        else:
            child_node = node.children[1]

        tac_ref = self.visit(child_node)
        self.values[id(node)] = self.get_semantic_value(child_node)
        return tac_ref
    def visit_operand(self, node):
        child_node = node.children[0]
        tac_ref = self.visit(child_node)
        self.values[id(node)] = self.get_semantic_value(child_node)
        return tac_ref
    def get_type(self, node_or_value):
        if isinstance(node_or_value, tuple) and len(node_or_value) >= 2:
            return node_or_value[0]
        elif isinstance(node_or_value, str) and node_or_value in self.variable_types:
            return self.variable_types[node_or_value]
        elif isinstance(node_or_value, str):
            return "id"
        elif isinstance(node_or_value, int):
            return "integer"
        elif isinstance(node_or_value, float):
            return "point"
        elif isinstance(node_or_value, bool):
            return "state"
        elif isinstance(node_or_value, str) and (node_or_value.startswith('"') and node_or_value.endswith('"')):
            return "text"
        return "unknown"
    def visit_typecast_expression(self, node):
        children = node.children
        target_token = children[0]
        target_type = target_token.value.lower()
        line = target_token.line
        column = target_token.column
        inner_expr_node = children[2]

        inner_tac_ref = self.visit(inner_expr_node)

        inner_semantic_value = self.get_semantic_value(inner_expr_node)
        current_type, current_value = self.safe_extract_tuple_value(inner_semantic_value)

        result_semantic = ("unknown", None)
        try:
            casted_value = None
            final_type = target_type
            if current_type == "get" or str(current_type).startswith("g"):
                 casted_value = None
            elif target_type == "integer":
                if current_type == "point": casted_value = int(current_value)
                elif current_type == "text": casted_value = int(current_value)
                elif current_type == "state": casted_value = 1 if current_value == "YES" else 0
                elif current_type == "integer": casted_value = current_value; final_type = current_type
                else: final_type = current_type; casted_value = current_value
            elif target_type == "point":
                if current_type == "integer": casted_value = float(current_value)
                elif current_type == "text": casted_value = float(current_value)
                elif current_type == "state": casted_value = 1.0 if current_value == "YES" else 0.0
                elif current_type == "point": casted_value = current_value; final_type = current_type
                else: final_type = current_type; casted_value = current_value
            elif target_type == "text":
                casted_value = str(current_value) if current_value is not None else ""
                final_type = "text"
            elif target_type == "state":
                if current_type in ("integer", "point"): casted_value = "YES" if current_value != 0 and current_value != 0.0 else "NO"
                elif current_type == "text": casted_value = "YES" if current_value != "" else "NO"
                elif current_type == "state": casted_value = current_value; final_type = current_type
                else: final_type = current_type; casted_value = current_value
            else:
                final_type = current_type; casted_value = current_value

            result_semantic = (final_type, casted_value)

        except ValueError as ve:
            error_str = str(ve)
            custom_msg = f"Error in typecasting: {error_str}"
            if "invalid literal for int()" in error_str: custom_msg = "Cannot convert provided text to integer."
            elif "could not convert string to float" in error_str: custom_msg = "Provided text is not a valid point."
            self.errors.append(SemanticError(custom_msg, line, column))
            result_semantic = ("unknown", None)
        except Exception as e:
            self.errors.append(SemanticError(f"Custom Error in typecasting: {str(e)}", line, column))
            result_semantic = ("unknown", None)

        temp = self.get_temp()
        self.variable_types[temp] = target_type
        self.emit('TYPECAST', inner_tac_ref, target_type, temp)

        self.values[id(node)] = result_semantic
        return temp
    def visit_varlist_declaration(self, node):
        children = node.children
        if len(children) < 2:
            return
        ident = children[1]
        line = ident.line
        column = ident.column
        name = ident.value
        extracted_value_semantic = ("empty", None)
        tac_ref_to_assign = None

        if not self.current_scope.define_variable(name, fixed=False, line=line, column=column):
            self.errors.append(RedeclarationError(name, line, column))
            if len(children) > 3: self.visit(children[3])
            return

        if len(children) >= 3 and children[2] and hasattr(children[2], 'data') and children[2].data == 'var_init':
             init_expr_node = children[2].children[1]
             tac_ref_to_assign = self.visit(init_expr_node)
             extracted_value_semantic = self.get_semantic_value(init_expr_node)
             self.emit('ASSIGN', tac_ref_to_assign, None, name)

        self.current_scope.variables[name].value = extracted_value_semantic
        self.variable_types[name] = extracted_value_semantic[0]

        if len(children) > 3:
            self.visit(children[3])
    def _is_get_function_call(self, node, prompt_ref=None):
        if hasattr(node, 'data') and node.data == 'id_usage':
            if (len(node.children) > 0 and hasattr(node.children[0], 'value') and node.children[0].value == 'get'):
                if (len(node.children) > 1 and hasattr(node.children[1], 'data') and node.children[1].data == 'func_call'):
                    if prompt_ref is not None and len(node.children[1].children) > 1:
                        args_node = node.children[1].children[1]
                        if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                            prompt_expr = self.get_value(args_node.children[0])
                            if isinstance(prompt_expr, str):
                                if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                                    prompt_ref = prompt_expr[1:-1]
                                else:
                                    prompt_ref = prompt_expr
                            elif isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                                if prompt_expr[0] == 'text':
                                    prompt_ref = prompt_expr[1]
                                else:
                                    prompt_ref = str(prompt_expr[1])
                    return True
        if hasattr(node, 'data') and node.data == 'expression':
            for child in node.children:
                if self._is_get_function_call(child, prompt_ref):
                    return True
        if hasattr(node, 'data') and node.data == 'variable_value':
            for child in node.children:
                if self._is_get_function_call(child, prompt_ref):
                    return True
        return False
    def visit_var_assign(self, node):
        children = node.children
        var_name = children[0].value
        has_accessor = False
        accessor_node = None
        if len(children) > 1 and children[1] and hasattr(children[1], 'data') and children[1].data == 'group_or_list':
            has_accessor = True
            accessor_node = children[1]
            accessor_node.parent = node
            self.visit(accessor_node)
        line = children[0].line
        column = children[0].column
        scope, symbol = self.current_scope.find_variable_scope(var_name)
        if symbol is None:
            self.errors.append(UndefinedIdentifierError(var_name, line, column))
            return
        if symbol.fixed:
            self.errors.append(FixedVarReassignmentError(var_name, line, column))
            return
        if has_accessor:
            var_value = getattr(symbol, "value", None)
            if var_value:
                var_type = var_value[0] if isinstance(var_value, tuple) else None
                if accessor_node.children[0].type == "LSQB" and var_type != "list" and var_type != "text":
                    self.errors.append(InvalidListAccessError(var_name, line, column))
                    return
                elif accessor_node.children[0].type == "LBRACE" and var_type != "group":
                    self.errors.append(InvalidGroupAccessError(var_name, line, column))
                    return
        if has_accessor:
            assign_op_idx = 2
            expr_idx = 3
        else:
            assign_op_idx = 1
            expr_idx = 2
        assign_op_node = children[assign_op_idx]
        if hasattr(assign_op_node, 'data'):
            op = assign_op_node.children[0].value
        else:
            op = assign_op_node.value if hasattr(assign_op_node, 'value') else '='
        expr_node = children[expr_idx]
        expr_val = self.get_value(expr_node)
        if has_accessor:
            pass
        else:
            if op == '=':
                if isinstance(expr_val, tuple):
                    self.emit('ASSIGN', expr_val[1], None, var_name)
                else:
                    self.emit('ASSIGN', expr_val, None, var_name)
            else:
                temp = self.get_temp()
                self.emit('ASSIGN', var_name, None, temp)
                rhs = expr_val[1] if isinstance(expr_val, tuple) else expr_val
                result_temp = self.get_temp()
                var_type = self.get_type(var_name)
                expr_type = expr_val[0] if isinstance(expr_val, tuple) else self.get_type(expr_val)
                if op == '+=':
                    if var_type == "text" or expr_type == "text":
                        self.emit('CONCAT', temp, rhs, result_temp)
                        self.variable_types[result_temp] = "text"
                    else:
                        self.emit('ADD', temp, rhs, result_temp)
                        if var_type == "point" or expr_type == "point":
                            self.variable_types[result_temp] = "point"
                        else:
                            self.variable_types[result_temp] = "integer"
                elif op == '-=':
                    if var_type == "text" or expr_type == "text":
                        self.emit('ERROR', "Cannot subtract from text", None, result_temp)
                    else:
                        self.emit('SUB', temp, rhs, result_temp)
                        if var_type == "point" or expr_type == "point":
                            self.variable_types[result_temp] = "point"
                        else:
                            self.variable_types[result_temp] = "integer"
                elif op == '*=':
                    if var_type == "text" or expr_type == "text":
                        self.emit('ERROR', "Cannot multiply text", None, result_temp)
                    else:
                        self.emit('MUL', temp, rhs, result_temp)
                        if var_type == "point" or expr_type == "point":
                            self.variable_types[result_temp] = "point"
                        else:
                            self.variable_types[result_temp] = "integer"
                elif op == '/=':
                    if var_type == "text" or expr_type == "text":
                        self.emit('ERROR', "Cannot divide text", None, result_temp)
                    else:
                        self.emit('DIV', temp, rhs, result_temp)
                        self.variable_types[result_temp] = "point"
                else:
                    self.emit('ASSIGN', rhs, None, result_temp)
                self.emit('ASSIGN', result_temp, None, var_name)
                if result_temp in self.variable_types:
                    self.variable_types[var_name] = self.variable_types[result_temp]
    def visit_id_usage(self, node):
        children = node.children
        ident = children[0]
        line = ident.line
        column = ident.column
        name = ident.value
        if len(children) > 1 and hasattr(children[1], 'data') and children[1].data == 'func_call':
            if name == 'get':
                prompt = ""
                if len(children[1].children) > 1:
                    args_node = children[1].children[1]
                    if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                        prompt_expr = self.get_value(args_node.children[0])
                        if isinstance(prompt_expr, str):
                            if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                                prompt = prompt_expr[1:-1]
                            else:
                                prompt = prompt_expr
                        elif isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                            if prompt_expr[0] == 'text':
                                prompt = prompt_expr[1]
                            else:
                                prompt = str(prompt_expr[1])
                temp = self.get_temp()
                self.emit('INPUT', prompt, None, temp)
                self.variable_types[temp] = 'text'
                result = ('text', temp)
                return result
            func_symbol = self.global_scope.lookup_function(name)
            if func_symbol is None:
                self.errors.append(FunctionNotDefinedError(name, line, column))
                result = ("unknown", None)
            else:
                expected = len(func_symbol.params)
                arg_values = self.evaluate_function_args(children[1])
                provided = len(arg_values)
                if expected != provided:
                    self.errors.append(ParameterMismatchError(name, expected, provided, line, column))
                    result = ("unknown", None)
                else:
                    if name in self.function_throw_expressions:
                        expr_node = self.function_throw_expressions[name]
                        old_scope = self.current_scope
                        self.push_scope()
                        for i, param_name in enumerate(func_symbol.params):
                            self.current_scope.define_variable(param_name, fixed=False)
                            self.current_scope.variables[param_name].value = arg_values[i]
                        result = self.get_value(expr_node)
                        self.function_returns[name] = result
                        self.pop_scope()
                    elif name in self.function_returns:
                        result = self.function_returns[name]
                    else:
                        result = ("empty", None)
            args = []
            if len(children[1].children) > 1:
                args_node = children[1].children[1]
                if hasattr(args_node, 'data') and args_node.data == 'args':
                    for child in args_node.children:
                        if hasattr(child, 'type') and child.type == 'COMMA':
                            continue
                        arg_val = self.get_value(child)
                        if arg_val is not None:
                            args.append(arg_val)
                elif hasattr(args_node, 'data') or hasattr(args_node, 'type'):
                    arg_val = self.get_value(args_node)
                    if arg_val is not None:
                        args.append(arg_val)
            for i, arg in enumerate(args):
                if isinstance(arg, tuple) and len(arg) >= 2:
                    self.emit('PARAM', arg[1], None, i)
                else:
                    self.emit('PARAM', arg, None, i)
            ret_temp = self.get_temp()
            self.emit('CALL', name, len(args), ret_temp)
            return ret_temp
        symbol = self.current_scope.lookup_variable(name)
        if symbol is None:
            self.errors.append(UndefinedIdentifierError(name, line, column))
            result_semantic = ("unknown", None)
            tac_ref = name
        else:
            result_semantic = getattr(symbol, "value", ("empty", None))
            tac_ref = name

        self.values[id(node)] = result_semantic
        return tac_ref
    def evaluate_function_args(self, func_call_node):
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
    def visit_group_or_list(self, node):
        if not node.children:
            return None
        is_list_access = node.children[0].type == "LSQB"
        index_expr = node.children[1]
        key_value = self.get_value(index_expr)
        parent = getattr(node, 'parent', None)
        if parent and hasattr(parent, 'data') and parent.data == 'id_usage':
            var_name = parent.children[0].value
            temp = self.get_temp()
            index_val = key_value
            if isinstance(key_value, tuple) and len(key_value) >= 2:
                index_val = key_value[1]
            if is_list_access:
                self.emit('LIST_ACCESS', var_name, index_val, temp)
            else:
                self.emit('GROUP_ACCESS', var_name, index_val, temp)
            var_symbol = self.current_scope.lookup_variable(var_name)
            if var_symbol:
                var_value = getattr(var_symbol, "value", None)
                if var_value:
                    var_type = var_value[0] if isinstance(var_value, tuple) else None
                    if is_list_access:
                        if var_type == "text":
                            text_value = var_value[1]
                            if key_value[0] == "integer":
                                idx = key_value[1]
                                if idx < 0:
                                    idx = len(text_value) + idx
                                if idx < 0 or idx >= len(text_value):
                                    line = getattr(index_expr, 'line', 0)
                                    column = getattr(index_expr, 'column', 0)
                                    self.errors.append(SemanticError(
                                        f"Text index {key_value[1]} out of range for variable '{var_name}'", 
                                        line, column))
                                    result = ("unknown", None)
                                else:
                                    result = ("text", text_value[idx])
                                return result
                        elif var_type == "list":
                            list_items = var_value[1]
                            if key_value[0] == "integer":
                                idx = key_value[1]
                                if idx < 0:
                                    idx = len(list_items) + idx
                                if idx < 0 or idx >= len(list_items):
                                    line = getattr(index_expr, 'line', 0)
                                    column = getattr(index_expr, 'column', 0)
                                    self.errors.append(ListIndexOutOfRangeError(
                                        var_name, key_value[1], line, column))
                                    result = ("unknown", None)
                                else:
                                    result = list_items[idx]
                                return result
                        elif var_type != "list" and var_type != "text":
                            line = parent.children[0].line if hasattr(parent.children[0], 'line') else 0
                            column = parent.children[0].column if hasattr(parent.children[0], 'column') else 0
                            self.errors.append(InvalidListAccessError(var_name, line, column))
                            return ("unknown", None)
                    else:
                        if var_type != "group":
                            line = parent.children[0].line if hasattr(parent.children[0], 'line') else 0
                            column = parent.children[0].column if hasattr(parent.children[0], 'column') else 0
                            self.errors.append(InvalidGroupAccessError(var_name, line, column))
                            return ("unknown", None)
                        else:
                            group_members = var_value[1]
                            result = None
                            found = False
                            for k, v in group_members:
                                if k[0] == key_value[0] and k[1] == key_value[1]:
                                    result = v
                                    found = True
                                    break
                            if not found:
                                line = getattr(index_expr, 'line', 0)
                                column = getattr(index_expr, 'column', 0)
                                self.errors.append(SemanticError(
                                    f"Key '{key_value[1]}' not found in group '{var_name}'",
                                    line, column))
                                result = ("unknown", None)
                            return result
            return temp
        return key_value
    def visit_show_statement(self, node):
        expr_node = node.children[2]
        expr_tac_ref = self.visit(expr_node)
        self.emit('PRINT', expr_tac_ref, None, None)
        return None
    def visit_checkif_statement(self, node):
        else_label = self.get_label()
        end_label = self.get_label()
        condition = self.get_value(node.children[2])
        self.check_boolean_expr(node.children[2], "checkif condition")
        self.emit('IFFALSE', condition, None, else_label)
        self.push_scope()
        self.visit(node.children[5])
        self.emit('GOTO', None, None, end_label)
        self.pop_scope()
        self.emit('LABEL', None, None, else_label)
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'recheck_statement':
                    self.visit_recheck_statement(child, end_label)
                elif child.data == 'otherwise_statement':
                    self.visit_otherwise_statement(child)
        self.emit('LABEL', None, None, end_label)
        return None
    def check_boolean_expr(self, expr_node, context):
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
    def visit_recheck_statement(self, node, end_label):
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        next_else_label = self.get_label()
        condition = self.get_value(node.children[2])
        self.check_boolean_expr(node.children[2], "recheck condition")
        self.emit('IFFALSE', condition, None, next_else_label)
        self.push_scope()
        self.visit(node.children[5])
        self.emit('GOTO', None, None, end_label)
        self.pop_scope()
        self.emit('LABEL', None, None, next_else_label)
        if len(node.children) > 7 and node.children[7]:
            self.visit_recheck_statement(node.children[7], end_label)
        return None
    def visit_otherwise_statement(self, node):
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        self.push_scope()
        self.visit(node.children[2])
        self.pop_scope()
        return None
    def visit_repeat_statement(self, node):
        start_label = self.get_label()
        end_label = self.get_label()
        self.push_loop(start_label, end_label)
        self.emit('LABEL', None, None, start_label)
        condition = self.get_value(node.children[2])
        self.check_boolean_expr(node.children[2], "repeat loop condition")
        self.emit('IFFALSE', condition, None, end_label)
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[4])
        self.exit_loop()
        self.pop_scope()
        self.emit('GOTO', None, None, start_label)
        self.emit('LABEL', None, None, end_label)
        self.pop_loop()
        return None
    def visit_do_repeat_statement(self, node):
        start_label = self.get_label()
        cond_label = self.get_label()
        end_label = self.get_label()
        self.push_loop(cond_label, end_label)
        self.emit('LABEL', None, None, start_label)
        self.push_scope()
        self.enter_loop()
        self.visit(node.children[2])
        self.exit_loop()
        self.pop_scope()
        self.emit('LABEL', None, None, cond_label)
        condition = self.get_value(node.children[6])
        self.check_boolean_expr(node.children[6], "do-repeat loop condition")
        self.emit('IFTRUE', condition, None, start_label)
        self.emit('LABEL', None, None, end_label)
        self.pop_loop()
        return None
    def visit_each_statement(self, node):
        init_label = self.get_label()
        cond_label = self.get_label()
        body_label = self.get_label()
        update_label = self.get_label()
        end_label = self.get_label()
        self.push_loop(update_label, end_label)
        if len(node.children) > 2 and node.children[2]:
            self.visit(node.children[2])
        self.emit('GOTO', None, None, cond_label)
        self.emit('LABEL', None, None, body_label)
        self.push_scope()
        self.enter_loop()
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'loop_block':
                self.visit(child)
                loop_body_found = True
                break
        if not loop_body_found:
            loop_body_index = 7
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        self.exit_loop()
        self.pop_scope()
        self.emit('LABEL', None, None, update_label)
        if len(node.children) > 5 and node.children[5]:
            self.visit(node.children[5])
        self.emit('GOTO', None, None, cond_label)
        self.emit('LABEL', None, None, cond_label)
        condition_expr = node.children[3]
        self.check_boolean_expr(condition_expr, "each loop condition")
        condition_temp = self.get_value(condition_expr)
        self.emit('IFTRUE', condition_temp, None, body_label)
        self.emit('LABEL', None, None, end_label)
        self.pop_loop()
        return None
    def visit_control_flow(self, node):
        stmt_type = node.children[0].value.lower()
        line = node.children[0].line
        column = node.children[0].column
        if not self.in_loop_block:
            self.errors.append(ControlFlowError(stmt_type, "loops", line, column))
            return None
        if not self.loop_stack:
            return None
        update_label, end_label = self.loop_stack[-1]
        if stmt_type == "exit":
            self.emit('GOTO', None, None, end_label)
        else:
            self.emit('GOTO', None, None, update_label)
        return None
    def visit_func_definition(self, node):
        func_token = node.children[1]
        func_name = func_token.value
        line = func_token.line
        column = func_token.column
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
            return
        self.function_returns[func_name] = ("empty", None)
        func_label = self.get_label()
        end_label = self.get_label()
        skip_label = self.get_label()
        self.emit('GOTO', None, None, skip_label)
        self.emit('FUNCTION', func_name, params, func_label)
        self.emit('LABEL', None, None, func_label)
        old_function = self.current_function
        self.current_function = func_name
        body_node = node.children[6]
        self.visit(body_node)
        self.current_function = old_function
        self.emit('LABEL', None, None, end_label)
        self.emit('RETURN', None, None, None)
        self.emit('LABEL', None, None, skip_label)
        return None
    def visit_throw_statement(self, node):
        if not self.current_function:
            throw_token = node.children[0]
            line = throw_token.line
            column = throw_token.column
            self.errors.append(ControlFlowError("throw", "functions", line, column))
            return None
        expr_node = node.children[1]
        self.function_throw_expressions[self.current_function] = expr_node
        self.has_return = True
        self.function_returns[self.current_function] = ("unknown", None)
        expr = self.get_value(node.children[1])
        val = expr[1] if isinstance(expr, tuple) else expr
        self.emit('RETURN', val, None, None)
        return None
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
    def visit_function_prog(self, node):
        for child in node.children:
            self.visit(child)
        return None