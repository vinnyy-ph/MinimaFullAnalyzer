from lark import Visitor
import uuid
class TACGenerator(Visitor):
    def __init__(self):
        super().__init__()
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.current_scope = "global"
        self.scope_stack = ["global"]
        self.loop_stack = []
        self.control_stack = []
        self.variable_types = {}
        self.values = {}
    def push_loop(self, start_label, end_label):
        """Push a new loop context onto the stack."""
        self.loop_stack.append((start_label, end_label))
    def pop_loop(self):
        """Pop the most recent loop context from the stack."""
        if self.loop_stack:
            return self.loop_stack.pop()
        return None
    def get_current_loop_labels(self):
        """Get the labels for the current innermost loop."""
        if self.loop_stack:
            return self.loop_stack[-1]
        return None, None
    def get_temp(self):
        """Generate a new temporary variable name."""
        self.temp_counter += 1
        return f"t{self.temp_counter}"
    def get_label(self):
        """Generate a new label for control flow."""
        self.label_counter += 1
        return f"L{self.label_counter}"
    def emit(self, op, arg1=None, arg2=None, result=None):
        """Emit a TAC instruction."""
        instruction = (op, arg1, arg2, result)
        self.instructions.append(instruction)
        return instruction
    def debug_print_tree(self, node, depth=0):
        """Debug function to print the AST structure"""
        if hasattr(node, 'data'):
            print(" " * depth + f"Node type: {node.data}")
            for child in node.children:
                self.debug_print_tree(child, depth + 2)
        elif hasattr(node, 'type'):
            value = getattr(node, 'value', '')
            print(" " * depth + f"Token: {node.type} = {value}")
        else:
            print(" " * depth + f"Unknown node: {node}")
    def generate(self, tree):
        print("DEBUG: AST Structure:")
        self.debug_print_tree(tree)
        """Main entry point to generate TAC from parse tree."""
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.variable_types = {}
        self.values = {}  
        self.visit(tree)
        return self.instructions
    def get_type(self, node_or_value):
        """Attempt to determine the type of a node or value."""
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
    def visit(self, tree):
        """Visit a node in the parse tree."""
        if not hasattr(tree, "data"):
            if hasattr(tree, "type"):
                return self.visit_token(tree)
            return None
        method_name = f"visit_{tree.data}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(tree)
        else:
            result = None
            for child in tree.children:
                if hasattr(child, "data") or hasattr(child, "type"):
                    result = self.visit(child)
            return result
    def visit_token(self, token):
        """Visit a token node."""
        if token.type == 'TEXTLITERAL':
            value = token.value
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return ('text', value)
        elif token.type == 'INTEGERLITERAL':
            return ('integer', int(token.value))
        elif token.type == 'NEGINTEGERLITERAL':
            return ('integer', -int(token.value[1:]))
        elif token.type == 'POINTLITERAL':
            return ('float', float(token.value))
        elif token.type == 'NEGPOINTLITERAL':
            return ('float', -float(token.value[1:]))
        elif token.type == 'STATELITERAL':
            return ('bool', token.value == "YES")
        elif token.type == 'EMPTY':
            return ('null', None)
        else:
            return ('id', token.value)
    def visit_start(self, node):
        """Start node is the root of the parse tree."""
        for child in node.children:
            self.visit(child)
        return None
    def visit_program(self, node):
        """Visit the program node."""
        for child in node.children:
            self.visit(child)
        return None
    def visit_program_block(self, node):
        """Visit a block of statements."""
        for child in node.children:
            self.visit(child)
        return None
    def visit_varlist_declaration(self, node):
        """Handle variable declarations."""
        var_name = node.children[1].value
        if len(node.children) >= 3 and node.children[2]:
            if hasattr(node.children[2], 'data') and node.children[2].data == 'var_init':
                if len(node.children[2].children) > 0:
                    init_expr_node = node.children[2].children[1]
                    get_prompt = None
                    if self._is_get_function_call(init_expr_node, get_prompt):
                        prompt = get_prompt if get_prompt else "Enter a value:"
                        temp = self.get_temp()
                        self.emit('INPUT', prompt, None, temp)
                        self.emit('ASSIGN', temp, None, var_name)
                        self.variable_types[var_name] = 'text'
                    else:
                        init_expr = self.visit(node.children[2].children[1])
                        if isinstance(init_expr, tuple) and init_expr[0] in ('id','integer','float','bool','string','text'):
                            self.emit('ASSIGN', init_expr[1], None, var_name)
                            self.variable_types[var_name] = init_expr[0]
                        else:
                            self.emit('ASSIGN', init_expr, None, var_name)
                            if isinstance(init_expr, str) and init_expr.startswith('t'):
                                pass
            if len(node.children) > 3 and node.children[3]:
                self.visit(node.children[3])
            return None
    def _is_get_function_call(self, node, prompt_ref=None):
        """Check if a node is or contains a get() function call.
        If prompt_ref is provided, it will be updated with the prompt string."""
        if hasattr(node, 'data') and node.data == 'id_usage':
            if (len(node.children) > 0 and 
                hasattr(node.children[0], 'value') and 
                node.children[0].value == 'get'):
                if (len(node.children) > 1 and 
                    hasattr(node.children[1], 'data') and 
                    node.children[1].data == 'func_call'):
                    if prompt_ref is not None and len(node.children[1].children) > 1:
                        args_node = node.children[1].children[1]
                        if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                            prompt_expr = self.visit(args_node.children[0])
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
    def visit_varlist_tail(self, node):
        """Handle additional variable declarations."""
        if not node or not hasattr(node, 'children') or len(node.children) < 2:
            return None
        var_name = node.children[1].value
        if len(node.children) >= 3 and node.children[2]:
            init_expr = self.visit(node.children[2])
            if isinstance(init_expr, tuple) and init_expr[0] in ('id','integer','float','bool','string','text'):
                self.emit('ASSIGN', init_expr[1], None, var_name)
                self.variable_types[var_name] = init_expr[0]
            else:
                self.emit('ASSIGN', init_expr, None, var_name)
        if len(node.children) > 3 and node.children[3]:
            self.visit(node.children[3])
        return None
    def visit_var_init(self, node):
        """Handle variable initialization."""
        if not node.children:
            return None
        if len(node.children) > 1:
            return self.visit(node.children[1])
        return None
    def visit_variable_value(self, node):
        """Visit a variable value node, handling both expressions and list literals."""
        if not node.children:
            return ('empty', None)
        if (len(node.children) >= 2 and 
            hasattr(node.children[0], 'type') and node.children[0].type == 'LSQB' and
            hasattr(node.children[1], 'type') and node.children[1].type == 'RSQB'):
            temp = self.get_temp()
            self.variable_types[temp] = "list"
            self.emit('LIST_CREATE', None, None, temp)
            return temp
        if (hasattr(node.children[0], 'type') and node.children[0].type == 'LSQB' and
            len(node.children) > 1):
            if hasattr(node.children[1], 'type') and node.children[1].type == 'RSQB':
                temp = self.get_temp()
                self.variable_types[temp] = "list"
                self.emit('LIST_CREATE', None, None, temp)
                return temp
            else:
                return self.visit(node.children[1])
        if hasattr(node.children[0], 'type') and node.children[0].type == 'GET':
            prompt_expr = None
            if len(node.children) >= 3:
                prompt_expr = self.visit(node.children[2])
            temp = self.get_temp()
            if isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                prompt_value = prompt_expr[1]
            elif isinstance(prompt_expr, str):
                if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                    prompt_value = prompt_expr[1:-1]  
                else:
                    prompt_value = prompt_expr
            else:
                prompt_value = "" 
            self.emit('INPUT', prompt_value, None, temp)
            self.variable_types[temp] = 'text' 
            return ('text', temp)
        if hasattr(node.children[0], 'data') and node.children[0].data == 'id_usage':
            id_usage_node = node.children[0]
            if (len(id_usage_node.children) > 0 and
                hasattr(id_usage_node.children[0], 'value') and
                id_usage_node.children[0].value == 'get'):
                if (len(id_usage_node.children) > 1 and
                    hasattr(id_usage_node.children[1], 'data') and
                    id_usage_node.children[1].data == 'func_call'):
                    prompt = "" 
                    if len(id_usage_node.children[1].children) > 1:
                        args_node = id_usage_node.children[1].children[1]
                        if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                            prompt_expr = self.visit(args_node.children[0])
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
                    return ('text', temp)  
        if hasattr(node.children[0], 'type') and node.children[0].type == 'LSQB':
            if len(node.children) > 1:
                return self.visit(node.children[1])
        return self.visit(node.children[0])
    def visit_list_value(self, node):
        """Handle list literals [expr, expr, ...].
        Creates a new list and appends each item to it."""
        temp = self.get_temp()
        self.variable_types[temp] = "list"
        self.emit('LIST_CREATE', None, None, temp)
        if node.children:
            first_item = self.visit(node.children[0])
            if isinstance(first_item, tuple) and len(first_item) >= 2:
                first_item_val = first_item[1]
            else:
                first_item_val = first_item
            self.emit('LIST_APPEND', temp, first_item_val, None)
            if len(node.children) > 1:
                self.visit_list_tail(node.children[1], temp)
        return temp
    def visit_list_tail(self, node, list_temp):
        """Handle additional items in a list literal.
        Called recursively to process all elements in a list."""
        if not node or not hasattr(node, 'children'):
            return
        if len(node.children) >= 2:
            item = self.visit(node.children[1])
            if isinstance(item, tuple) and len(item) >= 2:
                item_val = item[1]
            else:
                item_val = item
            self.emit('LIST_APPEND', list_temp, item_val, None)
        if len(node.children) > 2:
            self.visit_list_tail(node.children[2], list_temp)
    def visit_get_operand(self, node):
        """Visit a get_operand node (prompt inside get)."""
        if not node.children:
            return ('text', "")
        return self.visit(node.children[0])
    def visit_expression(self, node):
        """Visit an expression node."""
        if hasattr(node.children[0], 'data') and node.children[0].data == 'id_usage':
            id_usage_node = node.children[0]
            if (len(id_usage_node.children) > 0 and 
                hasattr(id_usage_node.children[0], 'value') and 
                id_usage_node.children[0].value == 'get'):
                if (len(id_usage_node.children) > 1 and 
                    hasattr(id_usage_node.children[1], 'data') and 
                    id_usage_node.children[1].data == 'func_call'):
                    prompt = "Enter a value:"
                    if len(id_usage_node.children[1].children) > 1:
                        args_node = id_usage_node.children[1].children[1]
                        if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                            prompt_expr = self.visit(args_node.children[0])
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
                    return ('text', temp)  
        result = self.visit(node.children[0])
        return result
    def visit_logical_or_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        left = self.visit(children[0])
        i = 1
        while i < len(children):
            right = self.visit(children[i+1])
            temp = self.get_temp()
            left_operand = left[1] if isinstance(left, tuple) else left
            right_operand = right[1] if isinstance(right, tuple) else right
            self.emit('OR', left_operand, right_operand, temp)
            left = temp
            i += 2
        return left
    def visit_logical_and_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        left = self.visit(children[0])
        i = 1
        while i < len(children):
            right = self.visit(children[i+1])
            temp = self.get_temp()
            left_operand = left[1] if isinstance(left, tuple) else left
            right_operand = right[1] if isinstance(right, tuple) else right
            self.emit('AND', left_operand, right_operand, temp)
            left = temp
            i += 2
        return left
    def visit_equality_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        left = self.visit(children[0])
        op = node.children[1].value
        right = self.visit(children[2])
        temp = self.get_temp()
        left_operand = left[1] if isinstance(left, tuple) else left
        right_operand = right[1] if isinstance(right, tuple) else right
        if op == "==":
            self.emit('EQ', left_operand, right_operand, temp)
        else:
            self.emit('NEQ', left_operand, right_operand, temp)
        return temp
    def visit_relational_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        left = self.visit(children[0])
        op = node.children[1].value
        right = self.visit(children[2])
        temp = self.get_temp()
        left_operand = left[1] if isinstance(left, tuple) else left
        right_operand = right[1] if isinstance(right, tuple) else right
        if op == "<":
            self.emit('LT', left_operand, right_operand, temp)
        elif op == "<=":
            self.emit('LE', left_operand, right_operand, temp)
        elif op == ">":
            self.emit('GT', left_operand, right_operand, temp)
        else:
            self.emit('GE', left_operand, right_operand, temp)
        return temp
    def visit_add_expr(self, node):
        children = node.children
        left = self.visit(children[0])
        i = 1
        while i < len(children):
            op = children[i].value  
            right = self.visit(children[i+1])
            temp = self.get_temp()
            left_operand = left[1] if isinstance(left, tuple) else left
            right_operand = right[1] if isinstance(right, tuple) else right
            left_type = left[0] if isinstance(left, tuple) else self.get_type(left)
            right_type = right[0] if isinstance(right, tuple) else self.get_type(right)
            if op == "+":
                if left_type == "list" or right_type == "list":
                    self.emit('ADD', left_operand, right_operand, temp)
                    self.variable_types[temp] = "list"
                elif left_type == "text" or right_type == "text":
                    self.emit('CONCAT', left_operand, right_operand, temp)
                    self.variable_types[temp] = "text"
                else:
                    self.emit('ADD', left_operand, right_operand, temp)
                    if left_type == "point" or right_type == "point" or left_type == "float" or right_type == "float":
                        self.variable_types[temp] = "point"
                    else:
                        self.variable_types[temp] = "integer"
            else:  
                if left_type == "text" or right_type == "text" or left_type == "list" or right_type == "list":
                    self.emit('ERROR', "Cannot subtract from text or list", None, temp)
                else:
                    self.emit('SUB', left_operand, right_operand, temp)
                    if left_type == "point" or right_type == "point" or left_type == "float" or right_type == "float":
                        self.variable_types[temp] = "point"
                    else:
                        self.variable_types[temp] = "integer"
            left = temp
            i += 2
        return left
    def visit_mul_expr(self, node):
        children = node.children
        left = self.visit(children[0])
        i = 1
        while i < len(children):
            op = children[i].value
            right = self.visit(children[i+1])
            temp = self.get_temp()
            left_operand = left[1] if isinstance(left, tuple) else left
            right_operand = right[1] if isinstance(right, tuple) else right
            left_type = left[0] if isinstance(left, tuple) else self.get_type(left)
            right_type = right[0] if isinstance(right, tuple) else self.get_type(right)
            if left_type == "text" or right_type == "text":
                self.emit('ERROR', f"Cannot use {op} with text", None, temp)
            else:
                if op == "*":
                    self.emit('MUL', left_operand, right_operand, temp)
                elif op == "/":
                    self.emit('DIV', left_operand, right_operand, temp)
                    self.variable_types[temp] = "point"
                else:  
                    self.emit('MOD', left_operand, right_operand, temp)
                if op != "/" and (left_type == "point" or right_type == "point" or 
                                left_type == "float" or right_type == "float"):
                    self.variable_types[temp] = "point"
                elif op != "/":
                    self.variable_types[temp] = "integer"
            left = temp
            i += 2
        return left
    def visit_pre_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        op = children[0].value
        expr = self.visit(children[1])
        temp = self.get_temp()
        operand = expr[1] if isinstance(expr, tuple) else expr
        if op == "!":
            self.emit('NOT', operand, None, temp)
            self.variable_types[temp] = "state"
        else:  
            self.emit('NEG', operand, None, temp)
            expr_type = expr[0] if isinstance(expr, tuple) else self.get_type(expr)
            if expr_type == "point" or expr_type == "float":
                self.variable_types[temp] = "point"
            else:
                self.variable_types[temp] = "integer"
        return temp
    def visit_primary_expr(self, node):
        if len(node.children) == 1:
            return self.visit(node.children[0])
        else:
            return self.visit(node.children[1])
    def visit_operand(self, node):
        if (hasattr(node.children[0], 'type') and node.children[0].type == 'GET' and
                len(node.children) >= 4 and  
                hasattr(node.children[1], 'type') and node.children[1].type == 'LPAREN' and
                hasattr(node.children[3], 'type') and node.children[3].type == 'RPAREN'):
            prompt_expr = self.visit(node.children[2])  
            if isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                prompt_value = prompt_expr[1]
            elif isinstance(prompt_expr, str):
                if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                    prompt_value = prompt_expr[1:-1]  
                else:
                    prompt_value = prompt_expr
            else:
                prompt_value = "" 
            temp = self.get_temp()
            self.emit('INPUT', prompt_value, None, temp)
            self.variable_types[temp] = 'text' 
            return ('text', temp)
        return self.visit(node.children[0])
    def visit_literals(self, node):
        return self.visit(node.children[0])
    def visit_id_usage(self, node):
        var_name = node.children[0].value
        if len(node.children) > 1 and hasattr(node.children[1], 'data') and node.children[1].data == 'func_call':
            if var_name == 'get':
                prompt = ""  
                if len(node.children[1].children) > 1:
                    args_node = node.children[1].children[1]
                    if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                        prompt_expr = self.visit(args_node.children[0])
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
                return ('text', temp)  
            args = []
            if len(node.children[1].children) > 1:
                args_node = node.children[1].children[1]
                if hasattr(args_node, 'data') and args_node.data == 'args':
                    for child in args_node.children:
                        if hasattr(child, 'type') and child.type == 'COMMA':
                            continue
                        arg_val = self.visit(child)
                        if arg_val is not None:
                            args.append(arg_val)
                elif hasattr(args_node, 'data') or hasattr(args_node, 'type'):
                    arg_val = self.visit(args_node)
                    if arg_val is not None:
                        args.append(arg_val)
            for i, arg in enumerate(args):
                if isinstance(arg, tuple) and len(arg) >= 2:
                    self.emit('PARAM', arg[1], None, i)
                else:
                    self.emit('PARAM', arg, None, i)
            ret_temp = self.get_temp()
            self.emit('CALL', var_name, len(args), ret_temp)
            return ret_temp
        for child in node.children[1:]:
            if hasattr(child, 'data') and child.data == 'group_or_list':
                index_expr = self.visit(child.children[1])
                temp = self.get_temp()
                is_list_access = child.children[0].type == "LSQB"
                if is_list_access:
                    if isinstance(index_expr, tuple) and index_expr[0] == 'id':
                        temp_idx = self.get_temp()
                        self.emit('ASSIGN', index_expr[1], None, temp_idx)
                        self.emit('LIST_ACCESS', var_name, temp_idx, temp)
                    else:
                        index_val = index_expr[1] if isinstance(index_expr, tuple) and len(index_expr) >= 2 else index_expr
                        self.emit('LIST_ACCESS', var_name, index_val, temp)
                else:
                    index_val = index_expr[1] if isinstance(index_expr, tuple) and len(index_expr) >= 2 else index_expr
                    self.emit('GROUP_ACCESS', var_name, index_val, temp)
                return temp
            if hasattr(child, 'data') and child.data == 'id_usagetail':
                for subchild in child.children:
                    if hasattr(subchild, 'data') and subchild.data == 'group_or_list' and subchild.children:
                        index_expr = self.visit(subchild.children[1])
                        temp = self.get_temp()
                        is_list_access = subchild.children[0].type == "LSQB"
                        index_val = index_expr
                        if isinstance(index_expr, tuple) and len(index_expr) >= 2:
                            index_val = index_expr[1] 
                        if is_list_access:
                            self.emit('LIST_ACCESS', var_name, index_val, temp)
                        else:
                            self.emit('GROUP_ACCESS', var_name, index_val, temp)
                        return temp
                    if hasattr(subchild, 'data') and subchild.data == 'unary_op':
                        if subchild.children and hasattr(subchild.children[0], 'type'):
                            op_type = subchild.children[0].type
                            if op_type == 'INC_OP':  
                                temp = self.get_temp()
                                self.emit('ASSIGN', var_name, None, temp)
                                self.emit('ADD', var_name, 1, var_name)
                                return temp
                            elif op_type == 'DEC_OP': 
                                temp = self.get_temp()
                                self.emit('ASSIGN', var_name, None, temp)
                                self.emit('SUB', var_name, 1, var_name)
                                return temp
        return ('id', var_name)
    def visit_id_usagetail(self, node):
        """Handle post-increment and post-decrement operations"""
        var_name = None
        if hasattr(node, 'parent') and hasattr(node.parent, 'children') and len(node.parent.children) > 0:
            if hasattr(node.parent.children[0], 'value'):
                var_name = node.parent.children[0].value
        if not var_name and hasattr(node, 'children') and len(node.children) > 0:
            if hasattr(node.children[0], 'value'):
                var_name = node.children[0].value
        if not var_name:
            return self.visit(node.children[0]) if node.children else None
        for child in node.children:
            if hasattr(child, 'data') and child.data == 'unary_op':
                if child.children and hasattr(child.children[0], 'type'):
                    op_type = child.children[0].type
                    if op_type == 'INC_OP':  
                        temp = self.get_temp()
                        self.emit('ASSIGN', var_name, None, temp)
                        self.emit('ADD', var_name, 1, var_name)
                        return temp
                    elif op_type == 'DEC_OP':  
                        temp = self.get_temp()
                        self.emit('ASSIGN', var_name, None, temp)
                        self.emit('SUB', var_name, 1, var_name)
                        return temp
        if node.children:
            for child in node.children:
                if hasattr(child, 'data'):
                    return self.visit(child)
        return None
    def visit_group_or_list(self, node, var_name=None):
        """Handle list or group indexing operations."""
        if not node.children:
            return None
        is_list_access = node.children[0].type == "LSQB"
        if var_name is None:
            parent = getattr(node, 'parent', None)
            if parent and hasattr(parent, 'data') and parent.data == 'id_usage':
                var_name = parent.children[0].value
            else:
                return None
        index_expr_node = node.children[1]
        if hasattr(index_expr_node, 'data') and index_expr_node.data == 'add_expr':
            index_expr = self.visit(index_expr_node)
        else:
            index_expr = self.visit(index_expr_node)
        if isinstance(index_expr, tuple) and len(index_expr) >= 2 and index_expr[0] == 'id':
            index_expr = index_expr[1]  
        temp = self.get_temp()
        if is_list_access:
            self.emit('LIST_ACCESS', var_name, index_expr, temp)
        else:
            self.emit('GROUP_ACCESS', var_name, index_expr, temp)
        return temp
    def visit_var_assign(self, node):
        """Handle variable assignments, including list element assignments."""
        children = node.children
        var_name = children[0].value
        has_accessor = False
        accessor_node = None
        accessor_expr = None
        if len(children) > 1 and children[1] and hasattr(children[1], 'data') and children[1].data == 'group_or_list':
            has_accessor = True
            accessor_node = children[1]
            if hasattr(accessor_node, 'children') and len(accessor_node.children) > 1:
                is_list_access = accessor_node.children[0].type == "LSQB"
                if is_list_access:
                    index_expr = self.visit(accessor_node.children[1])
                    if isinstance(index_expr, tuple) and index_expr[0] == 'id':
                        temp_idx = self.get_temp()
                        self.emit('ASSIGN', index_expr[1], None, temp_idx)
                        accessor_expr = temp_idx
                    else:
                        accessor_expr = index_expr
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
        expr_val = self.visit(expr_node)
        if isinstance(expr_val, tuple) and len(expr_val) >= 2:
            self.variable_types[var_name] = expr_val[0]
        if has_accessor and accessor_expr is not None:
            if op == '=':
                if isinstance(expr_val, tuple):
                    self.emit('LIST_SET', var_name, accessor_expr, expr_val[1])
                else:
                    self.emit('LIST_SET', var_name, accessor_expr, expr_val)
            else:
                temp = self.get_temp()
                self.emit('LIST_ACCESS', var_name, accessor_expr, temp)
                result_temp = self.get_temp()
                rhs = expr_val[1] if isinstance(expr_val, tuple) else expr_val
                if op == '+=':
                    self.emit('ADD', temp, rhs, result_temp)
                elif op == '-=':
                    self.emit('SUB', temp, rhs, result_temp)
                elif op == '*=':
                    self.emit('MUL', temp, rhs, result_temp)
                elif op == '/=':
                    self.emit('DIV', temp, rhs, result_temp)
                self.emit('LIST_SET', var_name, accessor_expr, result_temp)
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
                    if var_type == "list" or expr_type == "list":
                        self.emit('LIST_EXTEND', temp, rhs, var_name)
                        return None
                    elif var_type == "text" or expr_type == "text":
                        self.emit('CONCAT', temp, rhs, result_temp)
                        self.variable_types[result_temp] = "text"
                    else:
                        self.emit('ADD', temp, rhs, result_temp)
                        if var_type == "point" or expr_type == "point" or var_type == "float" or expr_type == "float":
                            self.variable_types[result_temp] = "point"
                        else:
                            self.variable_types[result_temp] = "integer"
                elif op == '-=':
                    self.emit('SUB', temp, rhs, result_temp)
                    if var_type == "point" or expr_type == "point" or var_type == "float" or expr_type == "float":
                        self.variable_types[result_temp] = "point"
                    else:
                        self.variable_types[result_temp] = "integer"
                elif op == '*=':
                    self.emit('MUL', temp, rhs, result_temp)
                    if var_type == "point" or expr_type == "point" or var_type == "float" or expr_type == "float":
                        self.variable_types[result_temp] = "point"
                    else:
                        self.variable_types[result_temp] = "integer"
                elif op == '/=':
                    self.emit('DIV', temp, rhs, result_temp)
                    self.variable_types[result_temp] = "point"
                if not (op == '+=' and (var_type == "list" or expr_type == "list")):
                    self.emit('ASSIGN', result_temp, None, var_name)
                    if result_temp in self.variable_types:
                        self.variable_types[var_name] = self.variable_types[result_temp]
        return None
    def visit_show_statement(self, node):
        """
        Generate TAC for show statements, properly handling list indexing in arguments.
        Structure: SHOW LPAREN expression RPAREN
        """
        expr = self.visit(node.children[2])
        if isinstance(expr, str) and expr.startswith('t'):
            val = expr
        else:
            val = expr[1] if isinstance(expr, tuple) and len(expr) >= 2 else expr
        self.emit('PRINT', val, None, None)
        return None
    def visit_func_definition(self, node):
        func_name = node.children[1].value
        param_names = []
        param_node = node.children[3]
        if hasattr(param_node, 'children'):
            for child in param_node.children:
                if hasattr(child, 'type') and child.type == 'IDENTIFIER':
                    param_names.append(child.value)
        elif hasattr(param_node, 'type') and param_node.type == 'IDENTIFIER':
            param_names.append(param_node.value)
        func_label = self.get_label()
        end_label = self.get_label()
        skip_label = self.get_label()
        self.emit('GOTO', None, None, skip_label)
        self.emit('FUNCTION', func_name, param_names, func_label)
        self.emit('LABEL', None, None, func_label)
        body_node = node.children[6]
        self.visit(body_node)
        self.emit('LABEL', None, None, end_label)
        self.emit('RETURN', None, None, None)
        self.emit('LABEL', None, None, skip_label)
        return None
    def visit_throw_statement(self, node):
        """
        Generate TAC for throw statement (function return)
        """
        expr = self.visit(node.children[1])
        val = expr[1] if isinstance(expr, tuple) else expr
        self.emit('RETURN', val, None, None)
        return None
    def visit_function_prog(self, node):
        for child in node.children:
            self.visit(child)
        return None
    def visit_typecast_expression(self, node):
        target_type = node.children[0].value.lower()
        expr = self.visit(node.children[2])
        temp = self.get_temp()
        self.variable_types[temp] = target_type
        if isinstance(expr, tuple):
            self.emit('TYPECAST', expr[1], target_type, temp)
        else:
            self.emit('TYPECAST', expr, target_type, temp)
        return temp
    def visit_loop_block(self, node):
        """Visit a block of statements in a loop."""
        for child in node.children:
            if hasattr(child, 'data') or hasattr(child, 'type'):
                self.visit(child)
        return None
    def visit_checkif_statement(self, node):
        """Generate TAC for if statements (checkif)."""
        else_label = self.get_label()
        end_label = self.get_label()
        condition = self.visit(node.children[2])
        self.emit('IFFALSE', condition, None, else_label)
        self.visit(node.children[5])  
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, else_label)
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'recheck_statement':
                    self.visit_recheck_statement(child, end_label)
                elif child.data == 'otherwise_statement':
                    self.visit_otherwise_statement(child)
        self.emit('LABEL', None, None, end_label)
        return None
    def visit_recheck_statement(self, node, end_label):
        """Generate TAC for else-if statements (recheck)."""
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        next_else_label = self.get_label()
        condition = self.visit(node.children[2])
        self.emit('IFFALSE', condition, None, next_else_label)
        self.visit(node.children[5])  
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, next_else_label)
        if len(node.children) > 7 and node.children[7]:
            self.visit_recheck_statement(node.children[7], end_label)
        return None
    def visit_otherwise_statement(self, node):
        """
        Generate TAC for else statements (otherwise).
        Structure: OTHERWISE LBRACE program_block RBRACE
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        self.visit(node.children[2])  
        return None
    def visit_repeat_statement(self, node):
        """
        Generate TAC for repeat loops (while loops).
        Structure: REPEAT LPAREN expression RPAREN LBRACE loop_block RBRACE
        """
        start_label = self.get_label()
        end_label = self.get_label()
        self.loop_stack.append((start_label, end_label))
        self.emit('LABEL', None, None, start_label)
        condition = self.visit(node.children[2])
        self.emit('IFFALSE', condition, None, end_label)
        self.visit(node.children[4])  
        self.emit('GOTO', None, None, start_label)
        self.emit('LABEL', None, None, end_label)
        self.loop_stack.pop()
        return None
    def visit_do_repeat_statement(self, node):
        """
        Generate TAC for do-repeat loops (do-while loops).
        Structure: DO LBRACE loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        start_label = self.get_label()
        cond_label = self.get_label()
        end_label = self.get_label()
        self.loop_stack.append((cond_label, end_label))
        self.emit('LABEL', None, None, start_label)
        self.visit(node.children[2])  
        self.emit('LABEL', None, None, cond_label)
        condition = self.visit(node.children[6])
        self.emit('IFTRUE', condition, None, start_label)
        self.emit('LABEL', None, None, end_label)
        self.loop_stack.pop()
        return None
    def visit_control_flow(self, node):
        """
        Handle exit and next statements within loops.
        """
        stmt_type = node.children[0].value.lower()  
        if not self.loop_stack:
            return None
        update_label, end_label = self.loop_stack[-1]
        if stmt_type == "exit":
            self.emit('GOTO', None, None, end_label)
        else:  
            self.emit('GOTO', None, None, update_label)
        return None
    def visit_each_statement(self, node):
        """
        Generate TAC for each loops (for loops).
        Structure: EACH LPAREN each_initialization expression SEMICOLON (expression | var_assign) RPAREN LBRACE loop_block RBRACE
        """
        init_label = self.get_label()  
        cond_label = self.get_label()  
        body_label = self.get_label()  
        update_label = self.get_label()  
        end_label = self.get_label()    
        self.loop_stack.append((update_label, end_label))
        if len(node.children) > 2 and node.children[2]:
            self.visit(node.children[2])  
        self.emit('GOTO', None, None, cond_label)
        self.emit('LABEL', None, None, body_label)
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
        self.emit('LABEL', None, None, update_label)
        if len(node.children) > 5 and node.children[5]:
            update_node = node.children[5]
            if hasattr(update_node, 'data') and update_node.data == 'id_usage':
                var_name = update_node.children[0].value
                for child in update_node.children[1:]:
                    if hasattr(child, 'data') and child.data == 'id_usagetail':
                        for subchild in child.children:
                            if hasattr(subchild, 'data') and subchild.data == 'unary_op':
                                if hasattr(subchild.children[0], 'type'):
                                    op_type = subchild.children[0].type
                                    if op_type == 'INC_OP':  
                                        self.emit('ADD', var_name, 1, var_name)
                                    elif op_type == 'DEC_OP':  
                                        self.emit('SUB', var_name, 1, var_name)
            if not (hasattr(update_node, 'data') and update_node.data == 'id_usage'):
                self.visit(update_node)
        self.emit('GOTO', None, None, cond_label)
        self.emit('LABEL', None, None, cond_label)
        condition_temp = self.visit(node.children[3])
        self.emit('IFTRUE', condition_temp, None, body_label)
        self.emit('LABEL', None, None, end_label)
        self.loop_stack.pop()
        return None
    def visit_repeat_statement(self, node):
        """
        Generate TAC for repeat loops (while loops).
        Structure: REPEAT LPAREN expression RPAREN LBRACE loop_block RBRACE
        """
        loop_start = self.get_label()
        loop_end = self.get_label()
        self.loop_stack.append((loop_start, loop_end))
        self.emit('LABEL', None, None, loop_start)
        condition_temp = self.visit(node.children[2])
        self.emit('IFFALSE', condition_temp, None, loop_end)
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'loop_block':
                self.visit(child)
                loop_body_found = True
                break
        if not loop_body_found:
            loop_body_index = 4  
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        self.emit('GOTO', None, None, loop_start)
        self.emit('LABEL', None, None, loop_end)
        self.loop_stack.pop()
        return None
    def visit_do_repeat_statement(self, node):
        """
        Generate TAC for do-repeat loops (do-while loops).
        Structure: DO LBRACE loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        loop_start = self.get_label()
        loop_cond = self.get_label()
        loop_end = self.get_label()
        self.loop_stack.append((loop_start, loop_end))
        self.emit('LABEL', None, None, loop_start)
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'loop_block':
                self.visit(child)
                loop_body_found = True
                break
        if not loop_body_found:
            loop_body_index = 2  
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        self.emit('LABEL', None, None, loop_cond)
        condition_node_index = 6  
        condition_temp = self.visit(node.children[condition_node_index])
        self.emit('IFTRUE', condition_temp, None, loop_start)
        self.emit('LABEL', None, None, loop_end)
        self.loop_stack.pop()
        return None
    def visit_each_func_statement(self, node):
        """
        Generate TAC for each loops within functions.
        Structure: EACH LPAREN each_initialization expression SEMICOLON (expression | var_assign) RPAREN LBRACE func_loop_block RBRACE
        """
        init_label = self.get_label()
        cond_label = self.get_label()
        body_label = self.get_label()
        update_label = self.get_label()
        end_label = self.get_label()
        self.loop_stack.append((update_label, end_label))
        self.emit('LABEL', None, None, init_label)
        self.visit(node.children[2])  
        self.emit('GOTO', None, None, cond_label)
        self.emit('LABEL', None, None, body_label)
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'func_loop_block':
                self.visit(child)
                loop_body_found = True
                break
        if not loop_body_found:
            loop_body_index = 7  
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        self.emit('LABEL', None, None, update_label)
        self.visit(node.children[5])  
        self.emit('GOTO', None, None, cond_label)
        self.emit('LABEL', None, None, cond_label)
        condition_temp = self.visit(node.children[3])
        self.emit('IFTRUE', condition_temp, None, body_label)
        self.emit('GOTO', None, None, end_label)  
        self.emit('LABEL', None, None, end_label)
        self.loop_stack.pop()
        return None
    def visit_repeat_func_statement(self, node):
        """
        Generate TAC for repeat loops within functions.
        Structure: REPEAT LPAREN expression RPAREN LBRACE func_loop_block RBRACE
        """
        loop_start = self.get_label()
        loop_end = self.get_label()
        self.loop_stack.append((loop_start, loop_end))
        self.emit('LABEL', None, None, loop_start)
        condition_temp = self.visit(node.children[2])
        self.emit('IFFALSE', condition_temp, None, loop_end)
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'func_loop_block':
                self.visit(child)
                loop_body_found = True
                break
        if not loop_body_found:
            loop_body_index = 4  
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        self.emit('GOTO', None, None, loop_start)
        self.emit('LABEL', None, None, loop_end)
        self.loop_stack.pop()
        return None
    def visit_do_repeat_func_statement(self, node):
        """
        Generate TAC for do-repeat loops within functions.
        Structure: DO LBRACE func_loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        loop_start = self.get_label()
        loop_cond = self.get_label()
        loop_end = self.get_label()
        self.loop_stack.append((loop_start, loop_end))
        self.emit('LABEL', None, None, loop_start)
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'func_loop_block':
                self.visit(child)
                loop_body_found = True
                break
        if not loop_body_found:
            loop_body_index = 2  
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        self.emit('LABEL', None, None, loop_cond)
        condition_node_index = 6  
        condition_temp = self.visit(node.children[condition_node_index])
        self.emit('IFTRUE', condition_temp, None, loop_start)
        self.emit('LABEL', None, None, loop_end)
        self.loop_stack.pop()
        return None
    def visit_loop_checkif_statement(self, node):
        """
        Generate TAC for if statements in loops.
        Similar to regular checkif but in a loop context.
        """
        else_label = self.get_label()
        end_label = self.get_label()
        condition = self.visit(node.children[2])
        self.emit('IFFALSE', condition, None, else_label)
        self.visit(node.children[5])  
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, else_label)
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'loop_recheck_statement':
                    self.visit_loop_recheck_statement(child, end_label)
                elif child.data == 'loop_otherwise_statement':
                    self.visit_loop_otherwise_statement(child)
        self.emit('LABEL', None, None, end_label)
        return None
    def visit_loop_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements in loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        next_else_label = self.get_label()
        condition = self.visit(node.children[2])
        self.emit('IFFALSE', condition, None, next_else_label)
        self.visit(node.children[5])  
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, next_else_label)
        if len(node.children) > 7 and node.children[7]:
            self.visit_loop_recheck_statement(node.children[7], end_label)
        return None
    def visit_loop_otherwise_statement(self, node):
        """
        Generate TAC for else statements in loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        self.visit(node.children[2])  
        return None
    def visit_switch_statement(self, node):
        """
        Generate TAC for switch statements.
        Structure: SWITCH LPAREN expression RPAREN LBRACE CASE literals COLON program case_tail default RBRACE
        """
        end_label = self.get_label()
        switch_expr = self.visit(node.children[2])
        switch_expr_val = switch_expr[1] if isinstance(switch_expr, tuple) and len(switch_expr) >= 2 else switch_expr
        case_value = self.visit(node.children[6])
        comp_temp = self.get_temp()
        self.emit('EQ', switch_expr_val, case_value[1] if isinstance(case_value, tuple) else case_value, comp_temp)
        next_case_label = self.get_label()
        self.emit('IFFALSE', comp_temp, None, next_case_label)
        self.visit(node.children[8])
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, next_case_label)
        if len(node.children) > 9 and node.children[9]:
            self.visit_case_tail(node.children[9], switch_expr_val, end_label)
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])
        self.emit('LABEL', None, None, end_label)
        return None
    def visit_case_tail(self, node, switch_expr, end_label):
        """
        Generate TAC for additional cases in a switch statement.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 4:
            return None
        case_value = self.visit(node.children[1])
        comp_temp = self.get_temp()
        self.emit('EQ', switch_expr, case_value[1] if isinstance(case_value, tuple) else case_value, comp_temp)
        next_case_label = self.get_label()
        self.emit('IFFALSE', comp_temp, None, next_case_label)
        self.visit(node.children[3])
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, next_case_label)
        if len(node.children) > 4 and node.children[4]:
            self.visit_case_tail(node.children[4], switch_expr, end_label)
        return None
    def visit_func_checkif_statement(self, node):
        """
        Generate TAC for if statements in functions.
        Similar to regular checkif but in a function context.
        """
        else_label = self.get_label()
        end_label = self.get_label()
        condition = self.visit(node.children[2])
        self.emit('IFFALSE', condition, None, else_label)
        self.visit(node.children[5])  
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, else_label)
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'func_recheck_statement':
                    self.visit_func_recheck_statement(child, end_label)
                elif child.data == 'func_otherwise_statement':
                    self.visit_func_otherwise_statement(child)
        self.emit('LABEL', None, None, end_label)
        return None
    def visit_func_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements in functions.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        next_else_label = self.get_label()
        condition = self.visit(node.children[2])
        self.emit('IFFALSE', condition, None, next_else_label)
        self.visit(node.children[5])  
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, next_else_label)
        if len(node.children) > 7 and node.children[7]:
            self.visit_func_recheck_statement(node.children[7], end_label)
        return None
    def visit_func_otherwise_statement(self, node):
        """
        Generate TAC for else statements in functions.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        self.visit(node.children[2])  
        return None
    def visit_func_loop_checkif_statement(self, node):
        """
        Generate TAC for if statements in function loops.
        """
        else_label = self.get_label()
        end_label = self.get_label()
        condition = self.visit(node.children[2])
        self.emit('IFFALSE', condition, None, else_label)
        self.visit(node.children[5])  
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, else_label)
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'func_loop_recheck_statement':
                    self.visit_func_loop_recheck_statement(child, end_label)
                elif child.data == 'func_loop_otherwise_statement':
                    self.visit_func_loop_otherwise_statement(child)
        self.emit('LABEL', None, None, end_label)
        return None
    def visit_func_loop_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements in function loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        next_else_label = self.get_label()
        condition = self.visit(node.children[2])
        self.emit('IFFALSE', condition, None, next_else_label)
        self.visit(node.children[5])  
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, next_else_label)
        if len(node.children) > 7 and node.children[7]:
            self.visit_func_loop_recheck_statement(node.children[7], end_label)
        return None
    def visit_func_loop_otherwise_statement(self, node):
        """
        Generate TAC for else statements in function loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        self.visit(node.children[2])  
        return None