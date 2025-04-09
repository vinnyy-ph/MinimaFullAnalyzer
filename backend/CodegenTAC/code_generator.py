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
        # For control flow
        self.loop_stack = []
        self.control_stack = []

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

    def generate(self, tree):
        """Main entry point to generate TAC from parse tree."""
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.visit(tree)
        return self.instructions

    def visit(self, tree):
        """Visit a node in the parse tree."""
        if not hasattr(tree, "data"):
            # It's a token
            if hasattr(tree, "type"):
                return self.visit_token(tree)
            return None
        
        method_name = f"visit_{tree.data}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(tree)
        else:
            # Default: visit all children
            result = None
            for child in tree.children:
                if hasattr(child, "data") or hasattr(child, "type"):
                    result = self.visit(child)
            return result

    def visit_token(self, token):
        """Visit a token node."""
        if token.type == 'TEXTLITERAL':
            return ('string', token.value.strip('"'))
        elif token.type == 'INTEGERLITERAL':
            return ('int', int(token.value))
        elif token.type == 'NEGINTEGERLITERAL':
            return ('int', -int(token.value[1:]))
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
        
        # Check if there's an initialization
        if len(node.children) >= 3 and node.children[2]:
            if hasattr(node.children[2], 'data') and node.children[2].data == 'var_init':
                if len(node.children[2].children) > 0:
                    init_expr = self.visit(node.children[2].children[1])
                    if isinstance(init_expr, tuple) and init_expr[0] in ('id','int','float','bool','string'):
                        self.emit('ASSIGN', init_expr[1], None, var_name)
                    else:
                        self.emit('ASSIGN', init_expr, None, var_name)
        
        # Visit the var_list tail if present
        if len(node.children) > 3 and node.children[3]:
            self.visit(node.children[3])
        
        return None

    def visit_varlist_tail(self, node):
        """Handle additional variable declarations."""
        if not node or not hasattr(node, 'children') or len(node.children) < 2:
            return None
        
        var_name = node.children[1].value
        
        if len(node.children) >= 3 and node.children[2]:
            init_expr = self.visit(node.children[2])
            if isinstance(init_expr, tuple) and init_expr[0] in ('id','int','float','bool','string'):
                self.emit('ASSIGN', init_expr[1], None, var_name)
            else:
                self.emit('ASSIGN', init_expr, None, var_name)
        
        # Recursively process more variables
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
        """Visit a variable value node."""
        if not node.children:
            return ('null', None)
        
        # GET operation
        if hasattr(node.children[0], 'type') and node.children[0].type == 'GET':
            prompt_expr = None
            if len(node.children) >= 3:
                prompt_expr = self.visit(node.children[2])
            temp = self.get_temp()
            self.emit('INPUT', prompt_expr[1] if isinstance(prompt_expr, tuple) else "Enter a value", None, temp)
            return temp
        
        # List or expression
        return self.visit(node.children[0])

    def visit_expression(self, node):
        return self.visit(node.children[0])

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
            op = node.children[i].value
            right = self.visit(children[i+1])
            temp = self.get_temp()
            left_operand = left[1] if isinstance(left, tuple) else left
            right_operand = right[1] if isinstance(right, tuple) else right
            if op == "+":
                self.emit('ADD', left_operand, right_operand, temp)
            else:
                self.emit('SUB', left_operand, right_operand, temp)
            left = temp
            i += 2
        return left

    def visit_mul_expr(self, node):
        children = node.children
        left = self.visit(children[0])
        i = 1
        while i < len(children):
            op = node.children[i].value
            right = self.visit(children[i+1])
            temp = self.get_temp()
            left_operand = left[1] if isinstance(left, tuple) else left
            right_operand = right[1] if isinstance(right, tuple) else right
            if op == "*":
                self.emit('MUL', left_operand, right_operand, temp)
            elif op == "/":
                self.emit('DIV', left_operand, right_operand, temp)
            else:
                self.emit('MOD', left_operand, right_operand, temp)
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
        else:  # "~"
            self.emit('NEG', operand, None, temp)
        return temp

    def visit_primary_expr(self, node):
        if len(node.children) == 1:
            return self.visit(node.children[0])
        else:
            return self.visit(node.children[1])

    def visit_operand(self, node):
        return self.visit(node.children[0])

    def visit_literals(self, node):
        return self.visit(node.children[0])

    def visit_id_usage(self, node):
        var_name = node.children[0].value
        
        # function call?
        if len(node.children) > 1 and hasattr(node.children[1], 'data') and node.children[1].data == 'func_call':
            # gather args
            args = []
            if len(node.children[1].children) > 1:
                args_node = node.children[1].children[1]
                if hasattr(args_node, 'data') and args_node.data == 'args':
                    for child in args_node.children:
                        if hasattr(child, 'type') and child.type == 'COMMA':
                            continue
                        arg_val = self.visit(child)
                        if isinstance(arg_val, tuple):
                            args.append(arg_val[1])
                        else:
                            args.append(arg_val)
            # Emit param instructions
            for i, a in enumerate(args):
                self.emit('PARAM', a, None, i)
            # Create a temp for return
            ret_temp = self.get_temp()
            self.emit('CALL', var_name, len(args), ret_temp)
            return ret_temp
        
        # normal variable usage
        return ('id', var_name)

    def visit_var_assign(self, node):
        var_name = node.children[0].value
        
        # direct assignment
        assign_op = node.children[1].value if hasattr(node.children[1], 'value') else '='
        expr_val = self.visit(node.children[2])
        
        if assign_op == '=':
            if isinstance(expr_val, tuple):
                self.emit('ASSIGN', expr_val[1], None, var_name)
            else:
                self.emit('ASSIGN', expr_val, None, var_name)
        else:
            # e.g. +=, -=, etc.
            temp = self.get_temp()
            self.emit('ASSIGN', var_name, None, temp)
            rhs = expr_val[1] if isinstance(expr_val, tuple) else expr_val
            result_temp = self.get_temp()
            if assign_op == '+=':
                self.emit('ADD', temp, rhs, result_temp)
            elif assign_op == '-=':
                self.emit('SUB', temp, rhs, result_temp)
            elif assign_op == '*=':
                self.emit('MUL', temp, rhs, result_temp)
            elif assign_op == '/=':
                self.emit('DIV', temp, rhs, result_temp)
            else:
                # fallback
                pass
            self.emit('ASSIGN', result_temp, None, var_name)
        
        return None

    def visit_show_statement(self, node):
        # show("some text");
        expr = self.visit(node.children[2])
        val = expr[1] if isinstance(expr, tuple) else expr
        self.emit('PRINT', val, None, None)
        return None

    def visit_func_definition(self, node):
        # function: func identifier(...) { ... }
        func_name = node.children[1].value
        
        # Create labels for function
        func_label = self.get_label()
        end_label = self.get_label()
        skip_label = self.get_label()
        
        # GOTO skip_label so we don't execute the function body now
        self.emit('GOTO', None, None, skip_label)

        # Mark function start
        self.emit('FUNCTION', func_name, None, func_label)
        self.emit('LABEL', None, None, func_label)

        # visit body
        body_node = node.children[6]
        self.visit(body_node)
        
        # At function end, emit label + a default return
        self.emit('LABEL', None, None, end_label)
        self.emit('RETURN', None, None, None)

        # Now skip over the function code
        self.emit('LABEL', None, None, skip_label)
        return None

    def visit_throw_statement(self, node):
        expr = self.visit(node.children[1])
        if isinstance(expr, tuple):
            self.emit('RETURN', expr[1], None, None)
        else:
            self.emit('RETURN', expr, None, None)
        return None

    def visit_function_prog(self, node):
        for child in node.children:
            self.visit(child)
        return None

    def visit_typecast_expression(self, node):
        target_type = node.children[0].value.lower()
        expr = self.visit(node.children[2])
        temp = self.get_temp()
        # In a real system, you'd have dedicated instructions or a type system
        self.emit('ASSIGN', expr[1] if isinstance(expr, tuple) else expr, None, temp)
        return temp

    def visit_control_flow(self, node):
        stmt_type = node.children[0].value.lower()  # "exit" or "next"
        if not self.loop_stack:
            return None
        start_label, end_label = self.loop_stack[-1]
        if stmt_type == "exit":
            self.emit('GOTO', None, None, end_label)
        else:
            self.emit('GOTO', None, None, start_label)
        return None

    def visit_loop_block(self, node):
        for child in node.children:
            self.visit(child)
        return None
