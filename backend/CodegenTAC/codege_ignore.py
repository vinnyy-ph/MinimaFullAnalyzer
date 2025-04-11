#ignore this COPILOT

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
            return ('text', token.value.strip('"'))
        elif token.type == 'INTEGERLITERAL':
            return ('integer', int(token.value))
        elif token.type == 'NEGINTEGERLITERAL':
            return ('integer', -int(token.value[1:]))
        elif token.type == 'POINTLITERAL':
            return ('point', float(token.value))
        elif token.type == 'NEGPOINTLITERAL':
            return ('point', -float(token.value[1:]))
        elif token.type == 'STATELITERAL':
            return ('state', token.value == "YES")
        elif token.type == 'EMPTY':
            return ('empty', None)
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
                    init_val = self.visit(node.children[2].children[1])
                    self.emit('ASSIGN', init_val[1] if isinstance(init_val, tuple) else init_val, None, var_name)
        
        # Visit the var_list tail if present
        if len(node.children) > 3 and node.children[3]:
            self.visit(node.children[3])
        
        return None

    def visit_varlist_tail(self, node):
        """Handle additional variable declarations."""
        if not node or not hasattr(node, 'children') or len(node.children) < 2:
            return None
        
        var_name = node.children[1].value
        
        if len(node.children) > 2 and node.children[2]:
            init_val = self.visit(node.children[2])
            self.emit('ASSIGN', init_val[1] if isinstance(init_val, tuple) else init_val, None, var_name)
        
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
            return ('empty', None)
        
        # GET operation
        if hasattr(node.children[0], 'type') and node.children[0].type == 'GET':
            prompt_expr = None
            if len(node.children) >= 3:
                prompt_expr = self.visit(node.children[2])
            temp = self.get_temp()
            prompt_value = prompt_expr[1] if isinstance(prompt_expr, tuple) else "Enter a value"
            self.emit('INPUT', prompt_value, None, temp)
            return ('text', temp)
        
        # List or expression
        return self.visit(node.children[0])

    def visit_expression(self, node):
        return self.visit(node.children[0])

    def state_to_number(self, state_val, target_type='integer'):
        """Convert state to numeric value - inline implementation"""
        temp = self.get_temp()
        if target_type == 'point':
            # Convert YES to 1.0, NO to 0.0
            true_label = self.get_label()
            end_label = self.get_label()
            
            # If state is true (YES), set temp to 1.0, otherwise 0.0
            self.emit('IFTRUE', state_val, None, true_label)
            self.emit('ASSIGN', 0.0, None, temp)
            self.emit('GOTO', None, None, end_label)
            self.emit('LABEL', None, None, true_label)
            self.emit('ASSIGN', 1.0, None, temp)
            self.emit('LABEL', None, None, end_label)
        else:
            # Convert YES to 1, NO to 0
            true_label = self.get_label()
            end_label = self.get_label()
            
            # If state is true (YES), set temp to 1, otherwise 0
            self.emit('IFTRUE', state_val, None, true_label)
            self.emit('ASSIGN', 0, None, temp)
            self.emit('GOTO', None, None, end_label)
            self.emit('LABEL', None, None, true_label)
            self.emit('ASSIGN', 1, None, temp)
            self.emit('LABEL', None, None, end_label)
        return temp

    def number_to_state(self, num_val):
        """Convert number to state - inline implementation"""
        temp = self.get_temp()
        zero_label = self.get_label()
        end_label = self.get_label()
        
        # If num_val is 0, set temp to false (NO), otherwise true (YES)
        self.emit('EQ', num_val, 0, zero_label)  # If num_val == 0, go to zero_label
        self.emit('ASSIGN', True, None, temp)    # Default: temp = true (YES)
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, zero_label)
        self.emit('ASSIGN', False, None, temp)   # At zero_label: temp = false (NO)
        self.emit('LABEL', None, None, end_label)
        return temp

    def text_to_number(self, text_val, as_float=False):
        """Convert text to number - implemented using primitives"""
        temp = self.get_temp()
        # We don't have direct string-to-number conversion in TAC
        # In a real implementation, this would involve custom parsing logic
        # Here, we'll just create a new temp and pretend it holds the converted value
        # In a real interpreter, this would need to be implemented
        
        # This is a dummy placeholder that produces a result
        # In a real scenario, this would be much more complex
        if as_float:
            self.emit('ASSIGN', 0.0, None, temp)  # Default conversion result
        else:
            self.emit('ASSIGN', 0, None, temp)  # Default conversion result
            
        return temp

    def text_to_state(self, text_val):
        """Convert text to state - empty is NO, non-empty is YES"""
        temp = self.get_temp()
        empty_label = self.get_label()
        end_label = self.get_label()
        
        # If text_val is empty, set temp to false (NO), otherwise true (YES)
        self.emit('EQ', text_val, "", empty_label)  # If text_val == "", go to empty_label
        self.emit('ASSIGN', True, None, temp)      # Default: temp = true (YES)
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, empty_label)
        self.emit('ASSIGN', False, None, temp)     # At empty_label: temp = false (NO)
        self.emit('LABEL', None, None, end_label)
        return temp

    def number_to_string(self, num_val):
        """Convert number to string representation"""
        # Since we can't actually convert numbers to strings in TAC,
        # we'll just emit a dummy operation to show the intent
        temp = self.get_temp()
        
        # In a real implementation, this would involve string conversion logic
        # For now, just store the original number in the temp
        self.emit('ASSIGN', num_val, None, temp)
        
        return temp

    def state_to_string(self, state_val):
        """Convert state to string - YES or NO"""
        temp = self.get_temp()
        true_label = self.get_label()
        end_label = self.get_label()
        
        # If state is true (YES), set temp to "YES", otherwise "NO"
        self.emit('IFTRUE', state_val, None, true_label)
        self.emit('ASSIGN', "NO", None, temp)
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, true_label)
        self.emit('ASSIGN', "YES", None, temp)
        self.emit('LABEL', None, None, end_label)
        
        return temp

    def convert_to_text(self, value_type, value):
        """Convert any value to text representation"""
        if value_type == 'text':
            # Already text, just return as is
            return value
        
        temp = self.get_temp()
        
        if value_type == 'integer' or value_type == 'point':
            # Number to string conversion
            result = self.number_to_string(value)
            self.emit('ASSIGN', result, None, temp)
        elif value_type == 'state':
            # State to string conversion
            result = self.state_to_string(value)
            self.emit('ASSIGN', result, None, temp)
        else:
            # Empty or unknown - convert to empty string
            self.emit('ASSIGN', "", None, temp)
            
        return temp

    def check_type_is_text(self, var_name):
        """Determine if a variable contains text - dummy implementation"""
        # Since we don't have direct type checking in TAC,
        # this is a placeholder that would typically involve runtime type checking
        # In a real implementation, this would need to access variable metadata
        
        # For now, just return a temporary that represents a boolean result
        temp = self.get_temp()
        self.emit('ASSIGN', False, None, temp)  # Assume not text by default
        return temp

    def convert_types_for_operation(self, left_type, left_val, right_type, right_val, op):
        """Convert types for binary operations based on semantic rules"""
        
        if op == "+" and (left_type == 'text' or right_type == 'text'):
            # String concatenation case
            left_text = left_val if left_type == 'text' else self.convert_to_text(left_type, left_val)
            right_text = right_val if right_type == 'text' else self.convert_to_text(right_type, right_val)
            return ('text', left_text, right_text)
            
        # Numeric operations
        use_float = (op == '/' or left_type == 'point' or right_type == 'point')
        result_type = 'point' if use_float else 'integer'
        
        # Convert left operand if needed
        if left_type == 'state':
            left_val = self.state_to_number(left_val, 'point' if use_float else 'integer')
        elif left_type == 'text':
            # Text to number conversion
            left_val = self.text_to_number(left_val, use_float)
        elif left_type == 'integer' and use_float:
            # Convert integer to float - since we can't actually do this in TAC,
            # we'll just emit a dummy temp that would hold the converted value
            temp = self.get_temp()
            # Just store the original value, in a real implementation this would convert to float
            self.emit('ASSIGN', float(left_val) if isinstance(left_val, (int, float)) else left_val, None, temp)
            left_val = temp
            
        # Convert right operand if needed
        if right_type == 'state':
            right_val = self.state_to_number(right_val, 'point' if use_float else 'integer')
        elif right_type == 'text':
            # Text to number conversion
            right_val = self.text_to_number(right_val, use_float)
        elif right_type == 'integer' and use_float:
            # Convert to float (dummy implementation)
            temp = self.get_temp()
            self.emit('ASSIGN', float(right_val) if isinstance(right_val, (int, float)) else right_val, None, temp)
            right_val = temp
            
        return (result_type, left_val, right_val)

    def visit_logical_or_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        i = 1
        while i < len(children):
            right = self.visit(children[i+1])
            right_type, right_val = right[0], right[1]
            
            # Convert both operands to state/boolean values
            if left_type != 'state':
                if left_type == 'integer' or left_type == 'point':
                    left_val = self.number_to_state(left_val)
                elif left_type == 'text':
                    left_val = self.text_to_state(left_val)
                else:
                    # Default for unknown types
                    temp = self.get_temp()
                    self.emit('ASSIGN', False, None, temp)
                    left_val = temp
                    
            if right_type != 'state':
                if right_type == 'integer' or right_type == 'point':
                    right_val = self.number_to_state(right_val)
                elif right_type == 'text':
                    right_val = self.text_to_state(right_val)
                else:
                    # Default for unknown types
                    temp = self.get_temp()
                    self.emit('ASSIGN', False, None, temp)
                    right_val = temp
            
            temp = self.get_temp()
            self.emit('OR', left_val, right_val, temp)
            left_type, left_val = 'state', temp
            i += 2
        
        return ('state', left_val)

    def visit_logical_and_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        i = 1
        while i < len(children):
            right = self.visit(children[i+1])
            right_type, right_val = right[0], right[1]
            
            # Convert both operands to state/boolean values
            if left_type != 'state':
                if left_type == 'integer' or left_type == 'point':
                    left_val = self.number_to_state(left_val)
                elif left_type == 'text':
                    left_val = self.text_to_state(left_val)
                else:
                    # Default for unknown types
                    temp = self.get_temp()
                    self.emit('ASSIGN', False, None, temp)
                    left_val = temp
                    
            if right_type != 'state':
                if right_type == 'integer' or right_type == 'point':
                    right_val = self.number_to_state(right_val)
                elif right_type == 'text':
                    right_val = self.text_to_state(right_val)
                else:
                    # Default for unknown types
                    temp = self.get_temp()
                    self.emit('ASSIGN', False, None, temp)
                    right_val = temp
            
            temp = self.get_temp()
            self.emit('AND', left_val, right_val, temp)
            left_type, left_val = 'state', temp
            i += 2
        
        return ('state', left_val)

    def visit_equality_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        op = node.children[1].value  # "==" or "!="
        
        right = self.visit(children[2])
        right_type, right_val = right[0], right[1]
        
        # Handle empty special case
        if left_type == 'empty' or right_type == 'empty':
            temp = self.get_temp()
            # Equal if both are empty
            if left_type == 'empty' and right_type == 'empty':
                self.emit('ASSIGN', True if op == "==" else False, None, temp)
            else:
                self.emit('ASSIGN', False if op == "==" else True, None, temp)
            return ('state', temp)
        
        # If types don't match, convert as needed
        if left_type != right_type:
            # If either is text, convert both to text
            if left_type == 'text' or right_type == 'text':
                if left_type != 'text':
                    left_val = self.convert_to_text(left_type, left_val)
                if right_type != 'text':
                    right_val = self.convert_to_text(right_type, right_val)
            # If either is point (float), convert both to point
            elif left_type == 'point' or right_type == 'point':
                _, left_val, right_val = self.convert_types_for_operation(left_type, left_val, right_type, right_val, '+')
        
        temp = self.get_temp()
        if op == "==":
            self.emit('EQ', left_val, right_val, temp)
        else:  # op == "!="
            self.emit('NEQ', left_val, right_val, temp)
        
        return ('state', temp)

    def visit_relational_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        op = node.children[1].value
        
        right = self.visit(children[2])
        right_type, right_val = right[0], right[1]
        
        # Determine target type - use point if either operand is point
        result_type, left_val, right_val = self.convert_types_for_operation(left_type, left_val, right_type, right_val, '+')
        
        temp = self.get_temp()
        if op == "<":
            self.emit('LT', left_val, right_val, temp)
        elif op == "<=":
            self.emit('LE', left_val, right_val, temp)
        elif op == ">":
            self.emit('GT', left_val, right_val, temp)
        else:  # op == ">="
            self.emit('GE', left_val, right_val, temp)
        
        return ('state', temp)

    def visit_add_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        i = 1
        while i < len(children):
            op = node.children[i].value
            
            right = self.visit(children[i+1])
            right_type, right_val = right[0], right[1]
            
            # Handle string concatenation or numeric addition
            if op == "+" and (left_type == 'text' or right_type == 'text'):
                # String concatenation case
                if left_type != 'text':
                    left_val = self.convert_to_text(left_type, left_val)
                if right_type != 'text':
                    right_val = self.convert_to_text(right_type, right_val)
                
                temp = self.get_temp()
                self.emit('CONCAT', left_val, right_val, temp)
                left_type, left_val = 'text', temp
            else:
                # Numeric operation
                result_type, left_num, right_num = self.convert_types_for_operation(left_type, left_val, right_type, right_val, op)
                temp = self.get_temp()
                if op == "+":
                    self.emit('ADD', left_num, right_num, temp)
                else:  # op == "-"
                    self.emit('SUB', left_num, right_num, temp)
                left_type, left_val = result_type, temp
            
            i += 2
        
        return (left_type, left_val)

    def visit_mul_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        i = 1
        while i < len(children):
            op = node.children[i].value
            
            right = self.visit(children[i+1])
            right_type, right_val = right[0], right[1]
            
            # Convert operands to appropriate numeric type
            result_type, left_num, right_num = self.convert_types_for_operation(left_type, left_val, right_type, right_val, op)
            
            temp = self.get_temp()
            if op == "*":
                self.emit('MUL', left_num, right_num, temp)
            elif op == "/":
                self.emit('DIV', left_num, right_num, temp)
            else:  # op == "%"
                self.emit('MOD', left_num, right_num, temp)
            
            left_type, left_val = result_type, temp
            i += 2
        
        return (left_type, left_val)

    def visit_pre_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        op = children[0].value
        
        expr = self.visit(children[1])
        expr_type, expr_val = expr[0], expr[1]
        
        temp = self.get_temp()
        if op == "!":
            # Logical negation - convert to state first if needed
            if expr_type != 'state':
                if expr_type == 'integer' or expr_type == 'point':
                    expr_val = self.number_to_state(expr_val)
                elif expr_type == 'text':
                    expr_val = self.text_to_state(expr_val)
                else:
                    # Default for unknown/empty
                    temp2 = self.get_temp()
                    self.emit('ASSIGN', False, None, temp2)
                    expr_val = temp2
            
            self.emit('NOT', expr_val, None, temp)
            return ('state', temp)
        else:  # op == "~"
            # Numeric negation
            if expr_type == 'state':
                # Convert YES to -1, NO to 0
                bool_to_int = self.state_to_number(expr_val, 'integer')
                self.emit('NEG', bool_to_int, None, temp)
                return ('integer', temp)
            elif expr_type in ('integer', 'point'):
                self.emit('NEG', expr_val, None, temp)
                return (expr_type, temp)
            elif expr_type == 'text':
                # Try to convert text to integer then negate
                num_val = self.text_to_number(expr_val, False)
                self.emit('NEG', num_val, None, temp)
                return ('integer', temp)
            else:
                # Default case
                self.emit('ASSIGN', 0, None, temp)
                return ('integer', temp)

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
            return ('unknown', ret_temp)  # We don't know the return type at compile time
        
        # normal variable usage
        return ('id', var_name)

    def visit_var_assign(self, node):
        var_name = node.children[0].value
        
        # direct assignment
        assign_op = node.children[1].value if hasattr(node.children[1], 'value') else '='
        expr_val = self.visit(node.children[2])
        expr_type, expr_value = expr_val if isinstance(expr_val, tuple) else ('unknown', expr_val)
        
        if assign_op == '=':
            self.emit('ASSIGN', expr_value, None, var_name)
        else:
            # e.g. +=, -=, etc.
            # Get existing variable
            var_temp = self.get_temp()
            self.emit('LOAD', var_name, None, var_temp)
            
            result_temp = self.get_temp()
            
            if assign_op == '+=':
                # Handle string concatenation special case
                is_text_label = self.get_label()
                not_text_label = self.get_label()
                end_label = self.get_label()
                
                # Check if either is text
                if expr_type == 'text':
                    # If expression is text, we know it's concatenation
                    var_as_text = self.convert_to_text('unknown', var_temp)
                    self.emit('CONCAT', var_as_text, expr_value, result_temp)
                else:
                    # Try numeric addition first
                    numeric_temp = self.get_temp()
                    self.emit('ADD', var_temp, expr_value, numeric_temp)
                    self.emit('ASSIGN', numeric_temp, None, result_temp)
                
                # Assign the result back to the variable
                self.emit('ASSIGN', result_temp, None, var_name)
                
            elif assign_op == '-=':
                self.emit('SUB', var_temp, expr_value, result_temp)
                self.emit('ASSIGN', result_temp, None, var_name)
            elif assign_op == '*=':
                self.emit('MUL', var_temp, expr_value, result_temp)
                self.emit('ASSIGN', result_temp, None, var_name)
            elif assign_op == '/=':
                self.emit('DIV', var_temp, expr_value, result_temp)
                self.emit('ASSIGN', result_temp, None, var_name)
        
        return None

    def visit_show_statement(self, node):
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
        target_type = node.children[0].value.lower()  # integer, point, state, text
        
        expr = self.visit(node.children[2])
        expr_type, expr_val = expr if isinstance(expr, tuple) else ('unknown', expr)
        
        temp = self.get_temp()
        
        if target_type == 'integer':
            if expr_type == 'point':
                # No direct float->int cast operation, assign as-is
                self.emit('ASSIGN', expr_val, None, temp)
            elif expr_type == 'text':
                # Convert text to integer (dummy implementation)
                result = self.text_to_number(expr_val, False)
                self.emit('ASSIGN', result, None, temp)
            elif expr_type == 'state':
                # State to integer: YES -> 1, NO -> 0
                result = self.state_to_number(expr_val, 'integer')
                self.emit('ASSIGN', result, None, temp)
            else:
                self.emit('ASSIGN', expr_val, None, temp)
            return ('integer', temp)
            
        elif target_type == 'point':
            if expr_type == 'integer':
                # No direct int->float cast operation, assign as-is
                self.emit('ASSIGN', expr_val, None, temp)
            elif expr_type == 'text':
                # Convert text to float (dummy implementation)
                result = self.text_to_number(expr_val, True)
                self.emit('ASSIGN', result, None, temp)
            elif expr_type == 'state':
                # State to float: YES -> 1.0, NO -> 0.0
                result = self.state_to_number(expr_val, 'point')
                self.emit('ASSIGN', result, None, temp)
            else:
                self.emit('ASSIGN', expr_val, None, temp)
            return ('point', temp)
            
        elif target_type == 'text':
            result = self.convert_to_text(expr_type, expr_val)
            self.emit('ASSIGN', result, None, temp)
            return ('text', temp)
            
        elif target_type == 'state':
            if expr_type in ('integer', 'point'):
                # Non-zero values become YES, zero becomes NO
                result = self.number_to_state(expr_val)
                self.emit('ASSIGN', result, None, temp)
            elif expr_type == 'text':
                # Empty string becomes NO, non-empty becomes YES
                result = self.text_to_state(expr_val)
                self.emit('ASSIGN', result, None, temp)
            else:
                self.emit('ASSIGN', expr_val, None, temp)
            return ('state', temp)
            
        return expr  # Return original if no conversion needed

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

    def visit_checkif_statement(self, node):
        """
        Generate TAC for if statements (checkif).
        Structure: CHECKIF LPAREN expression RPAREN LBRACE program_block RBRACE recheck_statement otherwise_statement
        """
        # Generate labels for different parts of the control flow
        else_label = self.get_label()
        end_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', cond_val, None, else_label)
        
        # Visit the if block
        self.visit(node.children[5])  # program_block
        
        # After executing the if block, skip the else block
        self.emit('GOTO', None, None, end_label)
        
        # Label for the else part (recheck or otherwise)
        self.emit('LABEL', None, None, else_label)
        
        # Visit recheck (else if) and otherwise (else) if present
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'recheck_statement':
                    self.visit_recheck_statement(child, end_label)
                elif child.data == 'otherwise_statement':
                    self.visit_otherwise_statement(child)
        
        # Label for the end of the if statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements (recheck).
        Structure: RECHECK LPAREN expression RPAREN LBRACE program_block RBRACE recheck_statement
        """
        # If this node is empty or doesn't have enough children, skip
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        
        # Generate label for the next else-if part
        next_else_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', cond_val, None, next_else_label)
        
        # Visit the else-if block
        self.visit(node.children[5])  # program_block
        
        # After executing the else-if block, skip to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next else part
        self.emit('LABEL', None, None, next_else_label)
        
        # Visit next recheck statement if present
        if len(node.children) > 7 and node.children[7]:
            self.visit_recheck_statement(node.children[7], end_label)
        
        return None

    def visit_otherwise_statement(self, node):
        """
        Generate TAC for else statements (otherwise).
        Structure: OTHERWISE LBRACE program_block RBRACE
        """
        # If this node is empty or doesn't have enough children, skip
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        # Visit the else block
        self.visit(node.children[2])  # program_block
        
        return None

    def visit_each_statement(self, node):
        """
        Generate TAC for each loops.
        Structure: EACH LPAREN each_initialization expression SEMICOLON expression RPAREN LBRACE loop_block RBRACE
        """
        # Generate labels for loop control
        start_label = self.get_label()
        cond_label = self.get_label()
        end_label = self.get_label()
        
        # Remember these labels for nested control flow statements (exit, next)
        self.loop_stack.append((start_label, end_label))
        
        # Initialization
        self.visit(node.children[2])  # each_initialization
        
        # Jump to condition check
        self.emit('GOTO', None, None, cond_label)
        
        # Label for loop start
        self.emit('LABEL', None, None, start_label)
        
        # Visit loop body
        self.visit(node.children[7])  # loop_block
        
        # Update expression
        self.visit(node.children[5])  # update expression
        
        # Condition check label
        self.emit('LABEL', None, None, cond_label)
        
        # Evaluate condition
        condition = self.visit(node.children[3])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # If condition is true, jump to start
        self.emit('IFTRUE', cond_val, None, start_label)
        
        # End label
        self.emit('LABEL', None, None, end_label)
        
        # Remove this loop from the stack
        self.loop_stack.pop()
        
        return None

    def visit_repeat_statement(self, node):
        """
        Generate TAC for repeat loops.
        Structure: REPEAT LPAREN expression RPAREN LBRACE loop_block RBRACE
        """
        # Generate labels for loop control
        start_label = self.get_label()
        end_label = self.get_label()
        
        # Remember these labels for nested control flow statements (exit, next)
        self.loop_stack.append((start_label, end_label))
        
        # Label for loop start
        self.emit('LABEL', None, None, start_label)
        
        # Evaluate condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # If condition is false, jump to end
        self.emit('IFFALSE', cond_val, None, end_label)
        
        # Visit loop body
        self.visit(node.children[4])  # loop_block
        
        # Jump back to start
        self.emit('GOTO', None, None, start_label)
        
        # End label
        self.emit('LABEL', None, None, end_label)
        
        # Remove this loop from the stack
        self.loop_stack.pop()
        
        return None

    def visit_do_repeat_statement(self, node):
        """
        Generate TAC for do-repeat loops.
        Structure: DO LBRACE loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        # Generate labels for loop control
        start_label = self.get_label()
        cond_label = self.get_label()
        end_label = self.get_label()
        
        # Remember these labels for nested control flow statements (exit, next)
        self.loop_stack.append((start_label, end_label))
        
        # Label for loop start
        self.emit('LABEL', None, None, start_label)
        
        # Visit loop body
        self.visit(node.children[2])  # loop_block
        
        # Condition label
        self.emit('LABEL', None, None, cond_label)
        
        # Evaluate condition
        condition = self.visit(node.children[6])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # If condition is true, jump to start
        self.emit('IFTRUE', cond_val, None, start_label)
        
        # End label
        self.emit('LABEL', None, None, end_label)
        
        # Remove this loop from the stack
        self.loop_stack.pop()
        
        return None

    def visit_loop_checkif_statement(self, node):
        """
        Generate TAC for if statements in loops.
        Similar to regular checkif but in a loop context.
        """
        # Generate labels for different parts of the control flow
        else_label = self.get_label()
        end_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', cond_val, None, else_label)
        
        # Visit the if block
        self.visit(node.children[5])  # loop_block
        
        # After executing the if block, skip the else block
        self.emit('GOTO', None, None, end_label)
        
        # Label for the else part (recheck or otherwise)
        self.emit('LABEL', None, None, else_label)
        
        # Visit recheck and otherwise if present
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'loop_recheck_statement':
                    self.visit_loop_recheck_statement(child, end_label)
                elif child.data == 'loop_otherwise_statement':
                    self.visit_loop_otherwise_statement(child)
        
        # Label for the end of the if statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_loop_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements in loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        
        # Generate label for the next else-if part
        next_else_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', cond_val, None, next_else_label)
        
        # Visit the else-if block
        self.visit(node.children[5])  # loop_block
        
        # After executing the else-if block, skip to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next else part
        self.emit('LABEL', None, None, next_else_label)
        
        # Visit next recheck statement if present
        if len(node.children) > 7 and node.children[7]:
            self.visit_loop_recheck_statement(node.children[7], end_label)
        
        return None

    def visit_loop_otherwise_statement(self, node):
        """
        Generate TAC for else statements in loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        # Visit the else block
        self.visit(node.children[2])  # loop_block
        
        return None

    def visit_func_checkif_statement(self, node):
        """
        Generate TAC for if statements in functions.
        Similar to regular checkif but in a function context.
        """
        # Generate labels for different parts of the control flow
        else_label = self.get_label()
        end_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', cond_val, None, else_label)
        
        # Visit the if block
        self.visit(node.children[5])  # function_prog
        
        # After executing the if block, skip the else block
        self.emit('GOTO', None, None, end_label)
        
        # Label for the else part (recheck or otherwise)
        self.emit('LABEL', None, None, else_label)
        
        # Visit recheck and otherwise if present
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'func_recheck_statement':
                    self.visit_func_recheck_statement(child, end_label)
                elif child.data == 'func_otherwise_statement':
                    self.visit_func_otherwise_statement(child)
        
        # Label for the end of the if statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_func_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements in functions.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        
        # Generate label for the next else-if part
        next_else_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', cond_val, None, next_else_label)
        
        # Visit the else-if block
        self.visit(node.children[5])  # function_prog
        
        # After executing the else-if block, skip to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next else part
        self.emit('LABEL', None, None, next_else_label)
        
        # Visit next recheck statement if present
        if len(node.children) > 7 and node.children[7]:
            self.visit_func_recheck_statement(node.children[7], end_label)
        
        return None

    def visit_func_otherwise_statement(self, node):
        """
        Generate TAC for else statements in functions.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        # Visit the else block
        self.visit(node.children[2])  # function_prog
        
        return None

    def visit_func_loop_checkif_statement(self, node):
        """
        Generate TAC for if statements in function loops.
        """
        # Generate labels for different parts of the control flow
        else_label = self.get_label()
        end_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', cond_val, None, else_label)
        
        # Visit the if block
        self.visit(node.children[5])  # func_loop_block
        
        # After executing the if block, skip the else block
        self.emit('GOTO', None, None, end_label)
        
        # Label for the else part (recheck or otherwise)
        self.emit('LABEL', None, None, else_label)
        
        # Visit recheck and otherwise if present
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'func_loop_recheck_statement':
                    self.visit_func_loop_recheck_statement(child, end_label)
                elif child.data == 'func_loop_otherwise_statement':
                    self.visit_func_loop_otherwise_statement(child)
        
        # Label for the end of the if statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_func_loop_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements in function loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        
        # Generate label for the next else-if part
        next_else_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', cond_val, None, next_else_label)
        
        # Visit the else-if block
        self.visit(node.children[5])  # func_loop_block
        
        # After executing the else-if block, skip to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next else part
        self.emit('LABEL', None, None, next_else_label)
        
        # Visit next recheck statement if present
        if len(node.children) > 7 and node.children[7]:
            self.visit_func_loop_recheck_statement(node.children[7], end_label)
        
        return None

    def visit_func_loop_otherwise_statement(self, node):
        """
        Generate TAC for else statements in function loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        # Visit the else block
        self.visit(node.children[2])  # func_loop_block
        
        return None

    def visit_switch_statement(self, node):
        """
        Generate TAC for switch statements.
        Structure: SWITCH LPAREN expression RPAREN LBRACE CASE literals COLON program case_tail default RBRACE
        """
        # Generate label for the end of the switch statement
        end_label = self.get_label()
        
        # Evaluate the switch expression
        switch_expr = self.visit(node.children[2])
        switch_type, switch_val = switch_expr if isinstance(switch_expr, tuple) else ('unknown', switch_expr)
        
        # Generate code for the first case
        case_value = self.visit(node.children[6])
        case_type, case_val = case_value if isinstance(case_value, tuple) else ('unknown', case_value)
        
        # Compare switch expression with case value
        comp_temp = self.get_temp()
        self.emit('EQ', switch_val, case_val, comp_temp)
        
        # Generate label for the next case
        next_case_label = self.get_label()
        
        # If comparison is false, skip to next case
        self.emit('IFFALSE', comp_temp, None, next_case_label)
        
        # Visit the case body
        self.visit(node.children[8])
        
        # After executing a case, jump to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next case
        self.emit('LABEL', None, None, next_case_label)
        
        # Visit the case_tail (remaining cases)
        if len(node.children) > 9 and node.children[9]:
            self.visit_case_tail(node.children[9], switch_val, end_label)
        
        # Visit default if present
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])
        
        # Label for the end of the switch statementfrom lark import Visitor
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
            return ('text', token.value.strip('"'))
        elif token.type == 'INTEGERLITERAL':
            return ('integer', int(token.value))
        elif token.type == 'NEGINTEGERLITERAL':
            return ('integer', -int(token.value[1:]))
        elif token.type == 'POINTLITERAL':
            return ('point', float(token.value))
        elif token.type == 'NEGPOINTLITERAL':
            return ('point', -float(token.value[1:]))
        elif token.type == 'STATELITERAL':
            return ('state', token.value == "YES")
        elif token.type == 'EMPTY':
            return ('empty', None)
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
                    init_val = self.visit(node.children[2].children[1])
                    self.emit('ASSIGN', init_val[1] if isinstance(init_val, tuple) else init_val, None, var_name)
        
        # Visit the var_list tail if present
        if len(node.children) > 3 and node.children[3]:
            self.visit(node.children[3])
        
        return None

    def visit_varlist_tail(self, node):
        """Handle additional variable declarations."""
        if not node or not hasattr(node, 'children') or len(node.children) < 2:
            return None
        
        var_name = node.children[1].value
        
        if len(node.children) > 2 and node.children[2]:
            init_val = self.visit(node.children[2])
            self.emit('ASSIGN', init_val[1] if isinstance(init_val, tuple) else init_val, None, var_name)
        
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
            return ('empty', None)
        
        # GET operation
        if hasattr(node.children[0], 'type') and node.children[0].type == 'GET':
            prompt_expr = None
            if len(node.children) >= 3:
                prompt_expr = self.visit(node.children[2])
            temp = self.get_temp()
            prompt_value = prompt_expr[1] if isinstance(prompt_expr, tuple) else "Enter a value"
            self.emit('INPUT', prompt_value, None, temp)
            return ('text', temp)
        
        # List or expression
        return self.visit(node.children[0])

    def visit_expression(self, node):
        return self.visit(node.children[0])

    def state_to_number(self, state_val, target_type='integer'):
        """Convert state to numeric value - inline implementation"""
        temp = self.get_temp()
        if target_type == 'point':
            # Convert YES to 1.0, NO to 0.0
            true_label = self.get_label()
            end_label = self.get_label()
            
            # If state is true (YES), set temp to 1.0, otherwise 0.0
            self.emit('IFTRUE', state_val, None, true_label)
            self.emit('ASSIGN', 0.0, None, temp)
            self.emit('GOTO', None, None, end_label)
            self.emit('LABEL', None, None, true_label)
            self.emit('ASSIGN', 1.0, None, temp)
            self.emit('LABEL', None, None, end_label)
        else:
            # Convert YES to 1, NO to 0
            true_label = self.get_label()
            end_label = self.get_label()
            
            # If state is true (YES), set temp to 1, otherwise 0
            self.emit('IFTRUE', state_val, None, true_label)
            self.emit('ASSIGN', 0, None, temp)
            self.emit('GOTO', None, None, end_label)
            self.emit('LABEL', None, None, true_label)
            self.emit('ASSIGN', 1, None, temp)
            self.emit('LABEL', None, None, end_label)
        return temp

    def number_to_state(self, num_val):
        """Convert number to state - inline implementation"""
        temp = self.get_temp()
        zero_label = self.get_label()
        end_label = self.get_label()
        
        # If num_val is 0, set temp to false (NO), otherwise true (YES)
        self.emit('EQ', num_val, 0, zero_label)  # If num_val == 0, go to zero_label
        self.emit('ASSIGN', True, None, temp)    # Default: temp = true (YES)
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, zero_label)
        self.emit('ASSIGN', False, None, temp)   # At zero_label: temp = false (NO)
        self.emit('LABEL', None, None, end_label)
        return temp

    def text_to_number(self, text_val, as_float=False):
        """Convert text to number - implemented using primitives"""
        temp = self.get_temp()
        # We don't have direct string-to-number conversion in TAC
        # In a real implementation, this would involve custom parsing logic
        # Here, we'll just create a new temp and pretend it holds the converted value
        # In a real interpreter, this would need to be implemented
        
        # This is a dummy placeholder that produces a result
        # In a real scenario, this would be much more complex
        if as_float:
            self.emit('ASSIGN', 0.0, None, temp)  # Default conversion result
        else:
            self.emit('ASSIGN', 0, None, temp)  # Default conversion result
            
        return temp

    def text_to_state(self, text_val):
        """Convert text to state - empty is NO, non-empty is YES"""
        temp = self.get_temp()
        empty_label = self.get_label()
        end_label = self.get_label()
        
        # If text_val is empty, set temp to false (NO), otherwise true (YES)
        self.emit('EQ', text_val, "", empty_label)  # If text_val == "", go to empty_label
        self.emit('ASSIGN', True, None, temp)      # Default: temp = true (YES)
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, empty_label)
        self.emit('ASSIGN', False, None, temp)     # At empty_label: temp = false (NO)
        self.emit('LABEL', None, None, end_label)
        return temp

    def number_to_string(self, num_val):
        """Convert number to string representation"""
        # Since we can't actually convert numbers to strings in TAC,
        # we'll just emit a dummy operation to show the intent
        temp = self.get_temp()
        
        # In a real implementation, this would involve string conversion logic
        # For now, just store the original number in the temp
        self.emit('ASSIGN', num_val, None, temp)
        
        return temp

    def state_to_string(self, state_val):
        """Convert state to string - YES or NO"""
        temp = self.get_temp()
        true_label = self.get_label()
        end_label = self.get_label()
        
        # If state is true (YES), set temp to "YES", otherwise "NO"
        self.emit('IFTRUE', state_val, None, true_label)
        self.emit('ASSIGN', "NO", None, temp)
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, true_label)
        self.emit('ASSIGN', "YES", None, temp)
        self.emit('LABEL', None, None, end_label)
        
        return temp

    def convert_to_text(self, value_type, value):
        """Convert any value to text representation"""
        if value_type == 'text':
            # Already text, just return as is
            return value
        
        temp = self.get_temp()
        
        if value_type == 'integer' or value_type == 'point':
            # Number to string conversion
            result = self.number_to_string(value)
            self.emit('ASSIGN', result, None, temp)
        elif value_type == 'state':
            # State to string conversion
            result = self.state_to_string(value)
            self.emit('ASSIGN', result, None, temp)
        else:
            # Empty or unknown - convert to empty string
            self.emit('ASSIGN', "", None, temp)
            
        return temp

    def check_type_is_text(self, var_name):
        """Determine if a variable contains text - dummy implementation"""
        # Since we don't have direct type checking in TAC,
        # this is a placeholder that would typically involve runtime type checking
        # In a real implementation, this would need to access variable metadata
        
        # For now, just return a temporary that represents a boolean result
        temp = self.get_temp()
        self.emit('ASSIGN', False, None, temp)  # Assume not text by default
        return temp

    def convert_types_for_operation(self, left_type, left_val, right_type, right_val, op):
        """Convert types for binary operations based on semantic rules"""
        
        if op == "+" and (left_type == 'text' or right_type == 'text'):
            # String concatenation case
            left_text = left_val if left_type == 'text' else self.convert_to_text(left_type, left_val)
            right_text = right_val if right_type == 'text' else self.convert_to_text(right_type, right_val)
            return ('text', left_text, right_text)
            
        # Numeric operations
        use_float = (op == '/' or left_type == 'point' or right_type == 'point')
        result_type = 'point' if use_float else 'integer'
        
        # Convert left operand if needed
        if left_type == 'state':
            left_val = self.state_to_number(left_val, 'point' if use_float else 'integer')
        elif left_type == 'text':
            # Text to number conversion
            left_val = self.text_to_number(left_val, use_float)
        elif left_type == 'integer' and use_float:
            # Convert integer to float - since we can't actually do this in TAC,
            # we'll just emit a dummy temp that would hold the converted value
            temp = self.get_temp()
            # Just store the original value, in a real implementation this would convert to float
            self.emit('ASSIGN', float(left_val) if isinstance(left_val, (int, float)) else left_val, None, temp)
            left_val = temp
            
        # Convert right operand if needed
        if right_type == 'state':
            right_val = self.state_to_number(right_val, 'point' if use_float else 'integer')
        elif right_type == 'text':
            # Text to number conversion
            right_val = self.text_to_number(right_val, use_float)
        elif right_type == 'integer' and use_float:
            # Convert to float (dummy implementation)
            temp = self.get_temp()
            self.emit('ASSIGN', float(right_val) if isinstance(right_val, (int, float)) else right_val, None, temp)
            right_val = temp
            
        return (result_type, left_val, right_val)

    def visit_logical_or_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        i = 1
        while i < len(children):
            right = self.visit(children[i+1])
            right_type, right_val = right[0], right[1]
            
            # Convert both operands to state/boolean values
            if left_type != 'state':
                if left_type == 'integer' or left_type == 'point':
                    left_val = self.number_to_state(left_val)
                elif left_type == 'text':
                    left_val = self.text_to_state(left_val)
                else:
                    # Default for unknown types
                    temp = self.get_temp()
                    self.emit('ASSIGN', False, None, temp)
                    left_val = temp
                    
            if right_type != 'state':
                if right_type == 'integer' or right_type == 'point':
                    right_val = self.number_to_state(right_val)
                elif right_type == 'text':
                    right_val = self.text_to_state(right_val)
                else:
                    # Default for unknown types
                    temp = self.get_temp()
                    self.emit('ASSIGN', False, None, temp)
                    right_val = temp
            
            temp = self.get_temp()
            self.emit('OR', left_val, right_val, temp)
            left_type, left_val = 'state', temp
            i += 2
        
        return ('state', left_val)

    def visit_logical_and_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        i = 1
        while i < len(children):
            right = self.visit(children[i+1])
            right_type, right_val = right[0], right[1]
            
            # Convert both operands to state/boolean values
            if left_type != 'state':
                if left_type == 'integer' or left_type == 'point':
                    left_val = self.number_to_state(left_val)
                elif left_type == 'text':
                    left_val = self.text_to_state(left_val)
                else:
                    # Default for unknown types
                    temp = self.get_temp()
                    self.emit('ASSIGN', False, None, temp)
                    left_val = temp
                    
            if right_type != 'state':
                if right_type == 'integer' or right_type == 'point':
                    right_val = self.number_to_state(right_val)
                elif right_type == 'text':
                    right_val = self.text_to_state(right_val)
                else:
                    # Default for unknown types
                    temp = self.get_temp()
                    self.emit('ASSIGN', False, None, temp)
                    right_val = temp
            
            temp = self.get_temp()
            self.emit('AND', left_val, right_val, temp)
            left_type, left_val = 'state', temp
            i += 2
        
        return ('state', left_val)

    def visit_equality_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        op = node.children[1].value  # "==" or "!="
        
        right = self.visit(children[2])
        right_type, right_val = right[0], right[1]
        
        # Handle empty special case
        if left_type == 'empty' or right_type == 'empty':
            temp = self.get_temp()
            # Equal if both are empty
            if left_type == 'empty' and right_type == 'empty':
                self.emit('ASSIGN', True if op == "==" else False, None, temp)
            else:
                self.emit('ASSIGN', False if op == "==" else True, None, temp)
            return ('state', temp)
        
        # If types don't match, convert as needed
        if left_type != right_type:
            # If either is text, convert both to text
            if left_type == 'text' or right_type == 'text':
                if left_type != 'text':
                    left_val = self.convert_to_text(left_type, left_val)
                if right_type != 'text':
                    right_val = self.convert_to_text(right_type, right_val)
            # If either is point (float), convert both to point
            elif left_type == 'point' or right_type == 'point':
                _, left_val, right_val = self.convert_types_for_operation(left_type, left_val, right_type, right_val, '+')
        
        temp = self.get_temp()
        if op == "==":
            self.emit('EQ', left_val, right_val, temp)
        else:  # op == "!="
            self.emit('NEQ', left_val, right_val, temp)
        
        return ('state', temp)

    def visit_relational_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        op = node.children[1].value
        
        right = self.visit(children[2])
        right_type, right_val = right[0], right[1]
        
        # Determine target type - use point if either operand is point
        result_type, left_val, right_val = self.convert_types_for_operation(left_type, left_val, right_type, right_val, '+')
        
        temp = self.get_temp()
        if op == "<":
            self.emit('LT', left_val, right_val, temp)
        elif op == "<=":
            self.emit('LE', left_val, right_val, temp)
        elif op == ">":
            self.emit('GT', left_val, right_val, temp)
        else:  # op == ">="
            self.emit('GE', left_val, right_val, temp)
        
        return ('state', temp)

    def visit_add_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        i = 1
        while i < len(children):
            op = node.children[i].value
            
            right = self.visit(children[i+1])
            right_type, right_val = right[0], right[1]
            
            # Handle string concatenation or numeric addition
            if op == "+" and (left_type == 'text' or right_type == 'text'):
                # String concatenation case
                if left_type != 'text':
                    left_val = self.convert_to_text(left_type, left_val)
                if right_type != 'text':
                    right_val = self.convert_to_text(right_type, right_val)
                
                temp = self.get_temp()
                self.emit('CONCAT', left_val, right_val, temp)
                left_type, left_val = 'text', temp
            else:
                # Numeric operation
                result_type, left_num, right_num = self.convert_types_for_operation(left_type, left_val, right_type, right_val, op)
                temp = self.get_temp()
                if op == "+":
                    self.emit('ADD', left_num, right_num, temp)
                else:  # op == "-"
                    self.emit('SUB', left_num, right_num, temp)
                left_type, left_val = result_type, temp
            
            i += 2
        
        return (left_type, left_val)

    def visit_mul_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        left = self.visit(children[0])
        left_type, left_val = left[0], left[1]
        
        i = 1
        while i < len(children):
            op = node.children[i].value
            
            right = self.visit(children[i+1])
            right_type, right_val = right[0], right[1]
            
            # Convert operands to appropriate numeric type
            result_type, left_num, right_num = self.convert_types_for_operation(left_type, left_val, right_type, right_val, op)
            
            temp = self.get_temp()
            if op == "*":
                self.emit('MUL', left_num, right_num, temp)
            elif op == "/":
                self.emit('DIV', left_num, right_num, temp)
            else:  # op == "%"
                self.emit('MOD', left_num, right_num, temp)
            
            left_type, left_val = result_type, temp
            i += 2
        
        return (left_type, left_val)

    def visit_pre_expr(self, node):
        children = node.children
        if len(children) == 1:
            return self.visit(children[0])
        
        op = children[0].value
        
        expr = self.visit(children[1])
        expr_type, expr_val = expr[0], expr[1]
        
        temp = self.get_temp()
        if op == "!":
            # Logical negation - convert to state first if needed
            if expr_type != 'state':
                if expr_type == 'integer' or expr_type == 'point':
                    expr_val = self.number_to_state(expr_val)
                elif expr_type == 'text':
                    expr_val = self.text_to_state(expr_val)
                else:
                    # Default for unknown/empty
                    temp2 = self.get_temp()
                    self.emit('ASSIGN', False, None, temp2)
                    expr_val = temp2
            
            self.emit('NOT', expr_val, None, temp)
            return ('state', temp)
        else:  # op == "~"
            # Numeric negation
            if expr_type == 'state':
                # Convert YES to -1, NO to 0
                bool_to_int = self.state_to_number(expr_val, 'integer')
                self.emit('NEG', bool_to_int, None, temp)
                return ('integer', temp)
            elif expr_type in ('integer', 'point'):
                self.emit('NEG', expr_val, None, temp)
                return (expr_type, temp)
            elif expr_type == 'text':
                # Try to convert text to integer then negate
                num_val = self.text_to_number(expr_val, False)
                self.emit('NEG', num_val, None, temp)
                return ('integer', temp)
            else:
                # Default case
                self.emit('ASSIGN', 0, None, temp)
                return ('integer', temp)

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
            return ('unknown', ret_temp)  # We don't know the return type at compile time
        
        # normal variable usage
        return ('id', var_name)

    def visit_var_assign(self, node):
        var_name = node.children[0].value
        
        # direct assignment
        assign_op = node.children[1].value if hasattr(node.children[1], 'value') else '='
        expr_val = self.visit(node.children[2])
        expr_type, expr_value = expr_val if isinstance(expr_val, tuple) else ('unknown', expr_val)
        
        if assign_op == '=':
            self.emit('ASSIGN', expr_value, None, var_name)
        else:
            # e.g. +=, -=, etc.
            # Get existing variable
            var_temp = self.get_temp()
            self.emit('LOAD', var_name, None, var_temp)
            
            result_temp = self.get_temp()
            
            if assign_op == '+=':
                # Handle string concatenation special case
                is_text_label = self.get_label()
                not_text_label = self.get_label()
                end_label = self.get_label()
                
                # Check if either is text
                if expr_type == 'text':
                    # If expression is text, we know it's concatenation
                    var_as_text = self.convert_to_text('unknown', var_temp)
                    self.emit('CONCAT', var_as_text, expr_value, result_temp)
                else:
                    # Try numeric addition first
                    numeric_temp = self.get_temp()
                    self.emit('ADD', var_temp, expr_value, numeric_temp)
                    self.emit('ASSIGN', numeric_temp, None, result_temp)
                
                # Assign the result back to the variable
                self.emit('ASSIGN', result_temp, None, var_name)
                
            elif assign_op == '-=':
                self.emit('SUB', var_temp, expr_value, result_temp)
                self.emit('ASSIGN', result_temp, None, var_name)
            elif assign_op == '*=':
                self.emit('MUL', var_temp, expr_value, result_temp)
                self.emit('ASSIGN', result_temp, None, var_name)
            elif assign_op == '/=':
                self.emit('DIV', var_temp, expr_value, result_temp)
                self.emit('ASSIGN', result_temp, None, var_name)
        
        return None

    def visit_show_statement(self, node):
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
        target_type = node.children[0].value.lower()  # integer, point, state, text
        
        expr = self.visit(node.children[2])
        expr_type, expr_val = expr if isinstance(expr, tuple) else ('unknown', expr)
        
        temp = self.get_temp()
        
        if target_type == 'integer':
            if expr_type == 'point':
                # No direct float->int cast operation, assign as-is
                self.emit('ASSIGN', expr_val, None, temp)
            elif expr_type == 'text':
                # Convert text to integer (dummy implementation)
                result = self.text_to_number(expr_val, False)
                self.emit('ASSIGN', result, None, temp)
            elif expr_type == 'state':
                # State to integer: YES -> 1, NO -> 0
                result = self.state_to_number(expr_val, 'integer')
                self.emit('ASSIGN', result, None, temp)
            else:
                self.emit('ASSIGN', expr_val, None, temp)
            return ('integer', temp)
            
        elif target_type == 'point':
            if expr_type == 'integer':
                # No direct int->float cast operation, assign as-is
                self.emit('ASSIGN', expr_val, None, temp)
            elif expr_type == 'text':
                # Convert text to float (dummy implementation)
                result = self.text_to_number(expr_val, True)
                self.emit('ASSIGN', result, None, temp)
            elif expr_type == 'state':
                # State to float: YES -> 1.0, NO -> 0.0
                result = self.state_to_number(expr_val, 'point')
                self.emit('ASSIGN', result, None, temp)
            else:
                self.emit('ASSIGN', expr_val, None, temp)
            return ('point', temp)
            
        elif target_type == 'text':
            result = self.convert_to_text(expr_type, expr_val)
            self.emit('ASSIGN', result, None, temp)
            return ('text', temp)
            
        elif target_type == 'state':
            if expr_type in ('integer', 'point'):
                # Non-zero values become YES, zero becomes NO
                result = self.number_to_state(expr_val)
                self.emit('ASSIGN', result, None, temp)
            elif expr_type == 'text':
                # Empty string becomes NO, non-empty becomes YES
                result = self.text_to_state(expr_val)
                self.emit('ASSIGN', result, None, temp)
            else:
                self.emit('ASSIGN', expr_val, None, temp)
            return ('state', temp)
            
        return expr  # Return original if no conversion needed

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

    def visit_checkif_statement(self, node):
        """
        Generate TAC for if statements (checkif).
        Structure: CHECKIF LPAREN expression RPAREN LBRACE program_block RBRACE recheck_statement otherwise_statement
        """
        # Generate labels for different parts of the control flow
        else_label = self.get_label()
        end_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', cond_val, None, else_label)
        
        # Visit the if block
        self.visit(node.children[5])  # program_block
        
        # After executing the if block, skip the else block
        self.emit('GOTO', None, None, end_label)
        
        # Label for the else part (recheck or otherwise)
        self.emit('LABEL', None, None, else_label)
        
        # Visit recheck (else if) and otherwise (else) if present
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'recheck_statement':
                    self.visit_recheck_statement(child, end_label)
                elif child.data == 'otherwise_statement':
                    self.visit_otherwise_statement(child)
        
        # Label for the end of the if statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements (recheck).
        Structure: RECHECK LPAREN expression RPAREN LBRACE program_block RBRACE recheck_statement
        """
        # If this node is empty or doesn't have enough children, skip
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        
        # Generate label for the next else-if part
        next_else_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', cond_val, None, next_else_label)
        
        # Visit the else-if block
        self.visit(node.children[5])  # program_block
        
        # After executing the else-if block, skip to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next else part
        self.emit('LABEL', None, None, next_else_label)
        
        # Visit next recheck statement if present
        if len(node.children) > 7 and node.children[7]:
            self.visit_recheck_statement(node.children[7], end_label)
        
        return None

    def visit_otherwise_statement(self, node):
        """
        Generate TAC for else statements (otherwise).
        Structure: OTHERWISE LBRACE program_block RBRACE
        """
        # If this node is empty or doesn't have enough children, skip
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        # Visit the else block
        self.visit(node.children[2])  # program_block
        
        return None

    def visit_each_statement(self, node):
        """
        Generate TAC for each loops.
        Structure: EACH LPAREN each_initialization expression SEMICOLON expression RPAREN LBRACE loop_block RBRACE
        """
        # Generate labels for loop control
        start_label = self.get_label()
        cond_label = self.get_label()
        end_label = self.get_label()
        
        # Remember these labels for nested control flow statements (exit, next)
        self.loop_stack.append((start_label, end_label))
        
        # Initialization
        self.visit(node.children[2])  # each_initialization
        
        # Jump to condition check
        self.emit('GOTO', None, None, cond_label)
        
        # Label for loop start
        self.emit('LABEL', None, None, start_label)
        
        # Visit loop body
        self.visit(node.children[7])  # loop_block
        
        # Update expression
        self.visit(node.children[5])  # update expression
        
        # Condition check label
        self.emit('LABEL', None, None, cond_label)
        
        # Evaluate condition
        condition = self.visit(node.children[3])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # If condition is true, jump to start
        self.emit('IFTRUE', cond_val, None, start_label)
        
        # End label
        self.emit('LABEL', None, None, end_label)
        
        # Remove this loop from the stack
        self.loop_stack.pop()
        
        return None

    def visit_repeat_statement(self, node):
        """
        Generate TAC for repeat loops.
        Structure: REPEAT LPAREN expression RPAREN LBRACE loop_block RBRACE
        """
        # Generate labels for loop control
        start_label = self.get_label()
        end_label = self.get_label()
        
        # Remember these labels for nested control flow statements (exit, next)
        self.loop_stack.append((start_label, end_label))
        
        # Label for loop start
        self.emit('LABEL', None, None, start_label)
        
        # Evaluate condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            if cond_type == 'integer' or cond_type == 'point':
                cond_val = self.number_to_state(cond_val)
            elif cond_type == 'text':
                cond_val = self.text_to_state(cond_val)
            else:
                # Default for unknown/empty types
                temp = self.get_temp()
                self.emit('ASSIGN', False, None, temp)
                cond_val = temp
        
        # If condition is false, jump to end
        self.emit('IFFALSE', cond_val, None, end_label)
        
        # Visit loop body
        self.visit(node.children[4])  # loop_block
        
        # Jump back to start
        self.emit('GOTO', None, None, start_label)
        
        # End label
        self.emit('LABEL', None, None, end_label)
        
        # Remove this loop from the stack
        self.loop_stack.pop()
        
        return None

    def visit_do_repeat_statement(self, node):
        """
        Generate TAC for do-repeat loops.
        Structure: DO LBRACE loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        # Generate labels for loop control
        start_label = self.get_label()
        cond_label = self.get_label()
        end_label = self.get_label()
        
        # Remember these labels for nested control flow statements (exit, next)
        self.loop_stack.append((start_label, end_label))
        
        # Label for loop start
        self.emit('LABEL', None, None, start_label)
        
        # Visit loop body
        self.visit(node.children[2])  # loop_block
        
        # Condition label
        self.emit('LABEL', None, None, cond_label)
        
        # Evaluate condition
        condition = self.visit(node.children[6])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            cond_val = self.number_to_state(cond_val)
        
        # If condition is true, jump to start
        self.emit('IFTRUE', cond_val, None, start_label)
        
        # End label
        self.emit('LABEL', None, None, end_label)
        
        # Remove this loop from the stack
        self.loop_stack.pop()
        
        return None

    def visit_loop_checkif_statement(self, node):
        """
        Generate TAC for if statements in loops.
        Similar to regular checkif but in a loop context.
        """
        # Generate labels for different parts of the control flow
        else_label = self.get_label()
        end_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            cond_val = self.number_to_state(cond_val)
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', cond_val, None, else_label)
        
        # Visit the if block
        self.visit(node.children[5])  # loop_block
        
        # After executing the if block, skip the else block
        self.emit('GOTO', None, None, end_label)
        
        # Label for the else part (recheck or otherwise)
        self.emit('LABEL', None, None, else_label)
        
        # Visit recheck and otherwise if present
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'loop_recheck_statement':
                    self.visit_loop_recheck_statement(child, end_label)
                elif child.data == 'loop_otherwise_statement':
                    self.visit_loop_otherwise_statement(child)
        
        # Label for the end of the if statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_loop_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements in loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        
        # Generate label for the next else-if part
        next_else_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            cond_val = self.number_to_state(cond_val)
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', cond_val, None, next_else_label)
        
        # Visit the else-if block
        self.visit(node.children[5])  # loop_block
        
        # After executing the else-if block, skip to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next else part
        self.emit('LABEL', None, None, next_else_label)
        
        # Visit next recheck statement if present
        if len(node.children) > 7 and node.children[7]:
            self.visit_loop_recheck_statement(node.children[7], end_label)
        
        return None

    def visit_loop_otherwise_statement(self, node):
        """
        Generate TAC for else statements in loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        # Visit the else block
        self.visit(node.children[2])  # loop_block
        
        return None

    def visit_func_checkif_statement(self, node):
        """
        Generate TAC for if statements in functions.
        Similar to regular checkif but in a function context.
        """
        # Generate labels for different parts of the control flow
        else_label = self.get_label()
        end_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            cond_val = self.number_to_state(cond_val)
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', cond_val, None, else_label)
        
        # Visit the if block
        self.visit(node.children[5])  # function_prog
        
        # After executing the if block, skip the else block
        self.emit('GOTO', None, None, end_label)
        
        # Label for the else part (recheck or otherwise)
        self.emit('LABEL', None, None, else_label)
        
        # Visit recheck and otherwise if present
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'func_recheck_statement':
                    self.visit_func_recheck_statement(child, end_label)
                elif child.data == 'func_otherwise_statement':
                    self.visit_func_otherwise_statement(child)
        
        # Label for the end of the if statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_func_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements in functions.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        
        # Generate label for the next else-if part
        next_else_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            cond_val = self.number_to_state(cond_val)
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', cond_val, None, next_else_label)
        
        # Visit the else-if block
        self.visit(node.children[5])  # function_prog
        
        # After executing the else-if block, skip to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next else part
        self.emit('LABEL', None, None, next_else_label)
        
        # Visit next recheck statement if present
        if len(node.children) > 7 and node.children[7]:
            self.visit_func_recheck_statement(node.children[7], end_label)
        
        return None

    def visit_func_otherwise_statement(self, node):
        """
        Generate TAC for else statements in functions.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        # Visit the else block
        self.visit(node.children[2])  # function_prog
        
        return None

    def visit_func_loop_checkif_statement(self, node):
        """
        Generate TAC for if statements in function loops.
        """
        # Generate labels for different parts of the control flow
        else_label = self.get_label()
        end_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            cond_val = self.number_to_state(cond_val)
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', cond_val, None, else_label)
        
        # Visit the if block
        self.visit(node.children[5])  # func_loop_block
        
        # After executing the if block, skip the else block
        self.emit('GOTO', None, None, end_label)
        
        # Label for the else part (recheck or otherwise)
        self.emit('LABEL', None, None, else_label)
        
        # Visit recheck and otherwise if present
        for child in node.children[6:]:
            if child and hasattr(child, 'data'):
                if child.data == 'func_loop_recheck_statement':
                    self.visit_func_loop_recheck_statement(child, end_label)
                elif child.data == 'func_loop_otherwise_statement':
                    self.visit_func_loop_otherwise_statement(child)
        
        # Label for the end of the if statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_func_loop_recheck_statement(self, node, end_label):
        """
        Generate TAC for else-if statements in function loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        
        # Generate label for the next else-if part
        next_else_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        cond_type, cond_val = condition if isinstance(condition, tuple) else ('unknown', condition)
        
        # Convert condition to boolean if needed
        if cond_type != 'state':
            cond_val = self.number_to_state(cond_val)
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', cond_val, None, next_else_label)
        
        # Visit the else-if block
        self.visit(node.children[5])  # func_loop_block
        
        # After executing the else-if block, skip to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next else part
        self.emit('LABEL', None, None, next_else_label)
        
        # Visit next recheck statement if present
        if len(node.children) > 7 and node.children[7]:
            self.visit_func_loop_recheck_statement(node.children[7], end_label)
        
        return None

    def visit_func_loop_otherwise_statement(self, node):
        """
        Generate TAC for else statements in function loops.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 3:
            return None
        
        # Visit the else block
        self.visit(node.children[2])  # func_loop_block
        
        return None

    def visit_switch_statement(self, node):
        """
        Generate TAC for switch statements.
        Structure: SWITCH LPAREN expression RPAREN LBRACE CASE literals COLON program case_tail default RBRACE
        """
        # Generate label for the end of the switch statement
        end_label = self.get_label()
        
        # Evaluate the switch expression
        switch_expr = self.visit(node.children[2])
        switch_type, switch_val = switch_expr if isinstance(switch_expr, tuple) else ('unknown', switch_expr)
        
        # Generate code for the first case
        case_value = self.visit(node.children[6])
        case_type, case_val = case_value if isinstance(case_value, tuple) else ('unknown', case_value)
        
        # Compare switch expression with case value
        comp_temp = self.get_temp()
        self.emit('EQ', switch_val, case_val, comp_temp)
        
        # Generate label for the next case
        next_case_label = self.get_label()
        
        # If comparison is false, skip to next case
        self.emit('IFFALSE', comp_temp, None, next_case_label)
        
        # Visit the case body
        self.visit(node.children[8])
        
        # After executing a case, jump to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next case
        self.emit('LABEL', None, None, next_case_label)
        
        # Visit the case_tail (remaining cases)
        if len(node.children) > 9 and node.children[9]:
            self.visit_case_tail(node.children[9], switch_val, end_label)
        
        # Visit default if present
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])
        
        # Label for the end of the switch statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_case_tail(self, node, switch_val, end_label):
        """
        Generate TAC for additional cases in a switch statement.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 4:
            return None
        
        # Get the case value
        case_value = self.visit(node.children[1])
        case_type, case_val = case_value if isinstance(case_value, tuple) else ('unknown', case_value)
        
        # Compare switch expression with case value
        comp_temp = self.get_temp()
        self.emit('EQ', switch_val, case_val, comp_temp)
        
        # Generate label for the next case
        next_case_label = self.get_label()
        
        # If comparison is false, skip to next case
        self.emit('IFFALSE', comp_temp, None, next_case_label)
        
        # Visit the case body
        self.visit(node.children[3])
        
        # After executing a case, jump to the end
        self.emit('GOTO', None, None, end_label)
        
        # Label for the next case
        self.emit('LABEL', None, None, next_case_label)
        
        # Visit the next case_tail if present
        if len(node.children) > 4 and node.children[4]:
            self.visit_case_tail(node.children[4], switch_val, end_label)
        
        return None