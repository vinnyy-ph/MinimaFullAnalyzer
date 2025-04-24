# backend/CodegenTAC/code_generator.py (fixed version)
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
        # Type tracking for variables
        self.variable_types = {}
        # Initialize values dictionary for node evaluation
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

    # Call this at the start of your generate method:
    def generate(self, tree):
        print("DEBUG: AST Structure:")
        self.debug_print_tree(tree)
        """Main entry point to generate TAC from parse tree."""
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.variable_types = {}
        self.values = {}  # Reset values dict
        self.visit(tree)
        return self.instructions

    def get_type(self, node_or_value):
        """Attempt to determine the type of a node or value."""
        if isinstance(node_or_value, tuple) and len(node_or_value) >= 2:
            # It's already a type-value tuple from visit_token
            return node_or_value[0]
        elif isinstance(node_or_value, str) and node_or_value in self.variable_types:
            # It's a variable name
            return self.variable_types[node_or_value]
        elif isinstance(node_or_value, str):
            return "id"  # Default for variable names
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
        
        # Check if there's an initialization
        if len(node.children) >= 3 and node.children[2]:
            if hasattr(node.children[2], 'data') and node.children[2].data == 'var_init':
                if len(node.children[2].children) > 0:
                    # First, try to find if there's a get() function call
                    init_expr_node = node.children[2].children[1]
                    get_prompt = None
                    
                    # Check for direct get() function call or through an expression
                    if self._is_get_function_call(init_expr_node, get_prompt):
                        # It's a get() function call - handle it directly
                        prompt = get_prompt if get_prompt else "Enter a value:"
                        temp = self.get_temp()
                        self.emit('INPUT', prompt, None, temp)
                        self.emit('ASSIGN', temp, None, var_name)
                        self.variable_types[var_name] = 'text'
                    else:
                        # Normal handling
                        init_expr = self.visit(node.children[2].children[1])
                        if isinstance(init_expr, tuple) and init_expr[0] in ('id','integer','float','bool','string','text'):
                            self.emit('ASSIGN', init_expr[1], None, var_name)
                            # Track variable type
                            self.variable_types[var_name] = init_expr[0]
                        else:
                            self.emit('ASSIGN', init_expr, None, var_name)
                            # Try to infer type if possible
                            if isinstance(init_expr, str) and init_expr.startswith('t'):
                                # It's a temporary variable, try to track its type
                                pass
            
            # Visit the var_list tail if present
            if len(node.children) > 3 and node.children[3]:
                self.visit(node.children[3])
            
            return None

    def _is_get_function_call(self, node, prompt_ref=None):
        """Check if a node is or contains a get() function call.
        If prompt_ref is provided, it will be updated with the prompt string."""
        
        # Direct id_usage with get function
        if hasattr(node, 'data') and node.data == 'id_usage':
            if (len(node.children) > 0 and 
                hasattr(node.children[0], 'value') and 
                node.children[0].value == 'get'):
                
                if (len(node.children) > 1 and 
                    hasattr(node.children[1], 'data') and 
                    node.children[1].data == 'func_call'):
                    
                    # Extract prompt if provided
                    if prompt_ref is not None and len(node.children[1].children) > 1:
                        args_node = node.children[1].children[1]
                        if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                            prompt_expr = self.visit(args_node.children[0])
                            
                            # Basic string
                            if isinstance(prompt_expr, str):
                                if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                                    prompt_ref = prompt_expr[1:-1]
                                else:
                                    prompt_ref = prompt_expr
                            # Typed tuple
                            elif isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                                if prompt_expr[0] == 'text':
                                    prompt_ref = prompt_expr[1]
                                else:
                                    prompt_ref = str(prompt_expr[1])
                    
                    return True
        
        # Check in expression nodes
        if hasattr(node, 'data') and node.data == 'expression':
            for child in node.children:
                if self._is_get_function_call(child, prompt_ref):
                    return True
        
        # Check in variable_value nodes
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
                # Track variable type
                self.variable_types[var_name] = init_expr[0]
            else:
                self.emit('ASSIGN', init_expr, None, var_name)
                # Try to infer type if possible
        
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

        # GET operation - direct token approach (original code)
        if hasattr(node.children[0], 'type') and node.children[0].type == 'GET':
            prompt_expr = None
            if len(node.children) >= 3:
                prompt_expr = self.visit(node.children[2])

            temp = self.get_temp()

            # Handle different types of prompt expressions
            if isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                prompt_value = prompt_expr[1]
            elif isinstance(prompt_expr, str):
                # Handle string literals correctly (remove quotes)
                if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                    prompt_value = prompt_expr[1:-1]
                else:
                    prompt_value = prompt_expr
            else:
                prompt_value = "" # Default prompt if none provided or invalid

            # Emit INPUT instruction with the prompt
            self.emit('INPUT', prompt_value, None, temp)

            # Return as a text type since input is always treated as text
            self.variable_types[temp] = 'text' # Ensure type is tracked
            return ('text', temp)

        # NEW: Check for get() function call through id_usage node
        if hasattr(node.children[0], 'data') and node.children[0].data == 'id_usage':
            id_usage_node = node.children[0]
            if (len(id_usage_node.children) > 0 and
                hasattr(id_usage_node.children[0], 'value') and
                id_usage_node.children[0].value == 'get'):

                # It's a get() function call
                if (len(id_usage_node.children) > 1 and
                    hasattr(id_usage_node.children[1], 'data') and
                    id_usage_node.children[1].data == 'func_call'):

                    # Default prompt
                    prompt = "" # Default prompt

                    # Extract prompt from arguments if available
                    if len(id_usage_node.children[1].children) > 1:
                        args_node = id_usage_node.children[1].children[1]
                        if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                            prompt_expr = self.visit(args_node.children[0])

                            # Handle string literals
                            if isinstance(prompt_expr, str):
                                if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                                    prompt = prompt_expr[1:-1]  # Remove the quotes
                                else:
                                    prompt = prompt_expr

                            # Handle tuples like ('text', 'hello')
                            elif isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                                if prompt_expr[0] == 'text':
                                    prompt = prompt_expr[1]
                                else:
                                    prompt = str(prompt_expr[1])

                    # Create temp variable and emit INPUT instruction
                    temp = self.get_temp()
                    self.emit('INPUT', prompt, None, temp)
                    self.variable_types[temp] = 'text' # Ensure type is tracked
                    return ('text', temp)  # Return as text type

        # Check if this is a list literal
        if hasattr(node.children[0], 'type') and node.children[0].type == 'LSQB':
            # This is a list literal [...]
            if len(node.children) > 1:
                # Visit the list_value node to get the list items
                return self.visit(node.children[1])

        # List or expression
        return self.visit(node.children[0])

    def visit_list_value(self, node):
        """Handle list literals [expr, expr, ...]."""
        # Create a temporary for the list
        temp = self.get_temp()
        
        # Mark this as a list type
        self.variable_types[temp] = "list"
        
        # Emit an instruction to create an empty list
        self.emit('LIST_CREATE', None, None, temp)
        
        # Add the first item
        first_item = self.visit(node.children[0])
        self.emit('LIST_APPEND', temp, first_item, None)
        
        # If there's a list_tail, visit it
        if len(node.children) > 1:
            self.visit_list_tail(node.children[1], temp)
        
        return temp

    def visit_list_tail(self, node, list_temp):
        """Handle additional items in a list literal."""
        if not node or not hasattr(node, 'children'):
            return
        
        # Skip the COMMA (first child) and add the expression (second child)
        if len(node.children) >= 2:
            item = self.visit(node.children[1])
            self.emit('LIST_APPEND', list_temp, item, None)
        
        # Process more items if they exist
        if len(node.children) > 2:
            self.visit_list_tail(node.children[2], list_temp)

    def visit_get_operand(self, node):
        """Visit a get_operand node (prompt inside get)."""
        if not node.children:
            return ('text', "")
        
        return self.visit(node.children[0])

    def visit_expression(self, node):
        """Visit an expression node."""
        # Check if this might be a get() function call
        if hasattr(node.children[0], 'data') and node.children[0].data == 'id_usage':
            id_usage_node = node.children[0]
            if (len(id_usage_node.children) > 0 and 
                hasattr(id_usage_node.children[0], 'value') and 
                id_usage_node.children[0].value == 'get'):
                
                # It's a get() function call, handle it directly
                if (len(id_usage_node.children) > 1 and 
                    hasattr(id_usage_node.children[1], 'data') and 
                    id_usage_node.children[1].data == 'func_call'):
                    
                    # Default prompt
                    prompt = "Enter a value:"
                    
                    # Extract prompt from arguments if available
                    if len(id_usage_node.children[1].children) > 1:
                        args_node = id_usage_node.children[1].children[1]
                        if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                            prompt_expr = self.visit(args_node.children[0])
                            
                            # Handle string literals
                            if isinstance(prompt_expr, str):
                                if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                                    prompt = prompt_expr[1:-1]  # Remove the quotes
                                else:
                                    prompt = prompt_expr
                            
                            # Handle tuples like ('text', 'hello')
                            elif isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                                if prompt_expr[0] == 'text':
                                    prompt = prompt_expr[1]
                                else:
                                    prompt = str(prompt_expr[1])
                    
                    # Create temp variable and emit INPUT instruction
                    temp = self.get_temp()
                    self.emit('INPUT', prompt, None, temp)
                    return ('text', temp)  # Return as text type
        
        # Normal handling if not a get() function call
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
            op = children[i].value  # PLUS or MINUS
            right = self.visit(children[i+1])
            temp = self.get_temp()
            
            # Get operand values
            left_operand = left[1] if isinstance(left, tuple) else left
            right_operand = right[1] if isinstance(right, tuple) else right
            
            # Get operand types
            left_type = left[0] if isinstance(left, tuple) else self.get_type(left)
            right_type = right[0] if isinstance(right, tuple) else self.get_type(right)
            
            # Handle different operand types
            if op == "+":
                # Special handling for lists
                if left_type == "list" or right_type == "list":
                    # Better handling for list concatenation
                    self.emit('ADD', left_operand, right_operand, temp)
                    # Track the result as list type
                    self.variable_types[temp] = "list"
                # Special handling for text concatenation
                elif left_type == "text" or right_type == "text":
                    # For text concatenation, use CONCAT operation instead of ADD
                    self.emit('CONCAT', left_operand, right_operand, temp)
                    # Track the result as text type
                    self.variable_types[temp] = "text"
                else:
                    # Normal addition for numeric types
                    self.emit('ADD', left_operand, right_operand, temp)
                    # If either operand is a point, result is a point
                    if left_type == "point" or right_type == "point" or left_type == "float" or right_type == "float":
                        self.variable_types[temp] = "point"
                    else:
                        self.variable_types[temp] = "integer"
            else:  # op == "-"
                # No subtraction for text or lists
                if left_type == "text" or right_type == "text" or left_type == "list" or right_type == "list":
                    # Generate an error instruction or a placeholder
                    self.emit('ERROR', "Cannot subtract from text or list", None, temp)
                else:
                    self.emit('SUB', left_operand, right_operand, temp)
                    # If either operand is a point, result is a point
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
            
            # Get operand values
            left_operand = left[1] if isinstance(left, tuple) else left
            right_operand = right[1] if isinstance(right, tuple) else right
            
            # Get operand types
            left_type = left[0] if isinstance(left, tuple) else self.get_type(left)
            right_type = right[0] if isinstance(right, tuple) else self.get_type(right)
            
            # Handle different operand types
            if left_type == "text" or right_type == "text":
                # Text doesn't support multiplication, division, or modulo
                self.emit('ERROR', f"Cannot use {op} with text", None, temp)
            else:
                if op == "*":
                    self.emit('MUL', left_operand, right_operand, temp)
                elif op == "/":
                    self.emit('DIV', left_operand, right_operand, temp)
                    # Division always results in a point (float)
                    self.variable_types[temp] = "point"
                else:  # op == "%"
                    self.emit('MOD', left_operand, right_operand, temp)
                
                # Set the result type for * and % operations
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
        else:  # "~"
            self.emit('NEG', operand, None, temp)
            # Determine result type based on operand
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
        # Check if this is a 'get' call with the GET token
        if (hasattr(node.children[0], 'type') and node.children[0].type == 'GET' and
                len(node.children) >= 4 and  # Has at least GET ( operand )
                hasattr(node.children[1], 'type') and node.children[1].type == 'LPAREN' and
                hasattr(node.children[3], 'type') and node.children[3].type == 'RPAREN'):

            # Extract the prompt from get_operand
            prompt_expr = self.visit(node.children[2])  # This should be the get_operand node

            # Get prompt value from the expression
            if isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                prompt_value = prompt_expr[1]
            elif isinstance(prompt_expr, str):
                if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                    prompt_value = prompt_expr[1:-1]  # Remove quotes
                else:
                    prompt_value = prompt_expr
            else:
                prompt_value = "" # Default prompt

            # Create a temporary variable for the input result
            temp = self.get_temp()

            # Generate the INPUT instruction
            self.emit('INPUT', prompt_value, None, temp)

            # Return the temp variable as text type
            self.variable_types[temp] = 'text' # Ensure type is tracked
            return ('text', temp)

        # Handle other operand types
        return self.visit(node.children[0])

    def visit_literals(self, node):
        return self.visit(node.children[0])

    def visit_id_usage(self, node):
        var_name = node.children[0].value

        # Function call?
        if len(node.children) > 1 and hasattr(node.children[1], 'data') and node.children[1].data == 'func_call':
            # Handle get() function specially
            if var_name == 'get':
                # Get prompt (default if none provided)
                prompt = ""  # Default prompt

                # Extract prompt from arguments if available
                if len(node.children[1].children) > 1:
                    args_node = node.children[1].children[1]
                    if hasattr(args_node, 'data') and args_node.data == 'args' and args_node.children:
                        prompt_expr = self.visit(args_node.children[0])

                        # Handle string literals
                        if isinstance(prompt_expr, str):
                            # If it's a string literal with quotes
                            if prompt_expr.startswith('"') and prompt_expr.endswith('"'):
                                prompt = prompt_expr[1:-1]  # Remove the quotes
                            else:
                                prompt = prompt_expr

                        # Handle tuples like ('text', 'hello')
                        elif isinstance(prompt_expr, tuple) and len(prompt_expr) >= 2:
                            # If it's a tuple with a type and a value
                            if prompt_expr[0] == 'text':
                                # Text type, use the value directly
                                prompt = prompt_expr[1]
                            else:
                                # Other type, convert to string
                                prompt = str(prompt_expr[1])

                # Create temp variable and emit INPUT instruction
                temp = self.get_temp()
                self.emit('INPUT', prompt, None, temp)
                self.variable_types[temp] = 'text' # Ensure type is tracked
                return ('text', temp)  # Return as text type (important!)
    
            # Regular function call
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
                    # Handle single argument that's not an 'args' node
                    arg_val = self.visit(args_node)
                    if arg_val is not None:
                        args.append(arg_val)

            # Emit PARAM instructions for each argument
            for i, arg in enumerate(args):
                # Ensure we get the actual value, not just a reference
                if isinstance(arg, tuple) and len(arg) >= 2:
                    self.emit('PARAM', arg[1], None, i)
                else:
                    self.emit('PARAM', arg, None, i)

            # Create temp for return
            ret_temp = self.get_temp()
            # Pass the number of arguments in the call
            self.emit('CALL', var_name, len(args), ret_temp)
            return ret_temp
        
        # Check for list/group access (indexing)
        for child in node.children[1:]:
            if hasattr(child, 'data') and child.data == 'group_or_list':
                # This is an indexing operation
                index_expr = self.visit(child.children[1])

                # Create a temporary variable for the result
                temp = self.get_temp()

                # Determine if this is list or group access
                is_list_access = child.children[0].type == "LSQB"

                # Extract the actual index value from tuples for variables
                index_val = index_expr
                if isinstance(index_expr, tuple) and len(index_expr) >= 2:
                     index_val = index_expr[1] # Use the value part

                if is_list_access:
                    # Handle list indexing
                    self.emit('LIST_ACCESS', var_name, index_val, temp)
                else:
                    # Handle group access (similar to dictionary)
                    self.emit('GROUP_ACCESS', var_name, index_val, temp)

                return temp
            
            # Check for id_usagetail (which may contain a group_or_list)
            if hasattr(child, 'data') and child.data == 'id_usagetail':
                for subchild in child.children:
                    if hasattr(subchild, 'data') and subchild.data == 'group_or_list' and subchild.children:
                        # This is an indexing operation
                        index_expr = self.visit(subchild.children[1])

                        # Create a temporary variable for the result
                        temp = self.get_temp()

                        # Determine if this is list or group access
                        is_list_access = subchild.children[0].type == "LSQB"

                        # Extract the actual index value from tuples for variables
                        index_val = index_expr
                        if isinstance(index_expr, tuple) and len(index_expr) >= 2:
                            index_val = index_expr[1] # Use the value part

                        if is_list_access:
                            # Handle list indexing
                            self.emit('LIST_ACCESS', var_name, index_val, temp)
                        else:
                            # Handle group access (similar to dictionary)
                            self.emit('GROUP_ACCESS', var_name, index_val, temp)

                        return temp

                    # Check if this is an increment/decrement operation
                    if hasattr(subchild, 'data') and subchild.data == 'unary_op':
                        if subchild.children and hasattr(subchild.children[0], 'type'):
                            op_type = subchild.children[0].type
                            if op_type == 'INC_OP':  # i++
                                # Save current value to temp variable
                                temp = self.get_temp()
                                self.emit('ASSIGN', var_name, None, temp)
                                # Increment the variable
                                self.emit('ADD', var_name, 1, var_name)
                                # Return the original value (post-increment)
                                return temp
                            elif op_type == 'DEC_OP': # i--
                                # Save current value to temp variable
                                temp = self.get_temp()
                                self.emit('ASSIGN', var_name, None, temp)
                                # Decrement the variable
                                self.emit('SUB', var_name, 1, var_name)
                                # Return the original value (post-decrement)
                                return temp

        # Normal variable usage
        return ('id', var_name)

    def visit_id_usagetail(self, node):
        """Handle post-increment and post-decrement operations"""
        # First, try to get the variable name from the parent node
        var_name = None
        if hasattr(node, 'parent') and hasattr(node.parent, 'children') and len(node.parent.children) > 0:
            if hasattr(node.parent.children[0], 'value'):
                var_name = node.parent.children[0].value
        
        # If we couldn't get the variable name from the parent, look for it in other ways
        if not var_name and hasattr(node, 'children') and len(node.children) > 0:
            if hasattr(node.children[0], 'value'):
                var_name = node.children[0].value
        
        if not var_name:
            # If we still don't have a variable name, just process the children normally
            return self.visit(node.children[0]) if node.children else None
        
        # Now check for post-increment/decrement operators
        for child in node.children:
            if hasattr(child, 'data') and child.data == 'unary_op':
                if child.children and hasattr(child.children[0], 'type'):
                    op_type = child.children[0].type
                    if op_type == 'INC_OP':  # i++
                        # First store current value to temp
                        temp = self.get_temp()
                        self.emit('ASSIGN', var_name, None, temp)
                        
                        # Then increment the variable
                        self.emit('ADD', var_name, 1, var_name)
                        
                        # Return the original value (post-increment)
                        return temp
                        
                    elif op_type == 'DEC_OP':  # i--
                        # First store current value to temp
                        temp = self.get_temp()
                        self.emit('ASSIGN', var_name, None, temp)
                        
                        # Then decrement the variable
                        self.emit('SUB', var_name, 1, var_name)
                        
                        # Return the original value (post-decrement)
                        return temp
        
        # Handle other id_usagetail nodes (function calls, etc.)
        if node.children:
            for child in node.children:
                if hasattr(child, 'data'):
                    return self.visit(child)
        
        return None

    def visit_group_or_list(self, node, var_name=None):
        """Handle list or group indexing operations."""
        if not node.children:
            return None
        
        # Determine if this is list access or group access
        is_list_access = node.children[0].type == "LSQB"
        
        # Get the variable name from the parent if not provided
        if var_name is None:
            parent = getattr(node, 'parent', None)
            if parent and hasattr(parent, 'data') and parent.data == 'id_usage':
                var_name = parent.children[0].value
            else:
                return None
        
        # Get the index expression
        index_expr_node = node.children[1]
        
        # Check if this is a complex expression like j+1
        if hasattr(index_expr_node, 'data') and index_expr_node.data == 'add_expr':
            # Handle complex expressions like j+1 by fully evaluating them first
            index_expr = self.visit(index_expr_node)
        else:
            # Simple index
            index_expr = self.visit(index_expr_node)
        
        # Extract the actual index value from tuples for variables
        if isinstance(index_expr, tuple) and len(index_expr) >= 2 and index_expr[0] == 'id':
            index_expr = index_expr[1]  # Just use the variable name
        
        # Create a temporary variable for the result
        temp = self.get_temp()
        
        # Generate appropriate access instruction
        if is_list_access:
            # Handle list indexing or string indexing
            self.emit('LIST_ACCESS', var_name, index_expr, temp)
        else:
            # Handle group access (similar to dictionary)
            self.emit('GROUP_ACCESS', var_name, index_expr, temp)
        
        return temp

    def visit_var_assign(self, node):
        children = node.children
        var_name = children[0].value
        
        # Check for list or group access
        has_accessor = False
        accessor_node = None
        
        # Check if the second child is a group_or_list node
        if len(children) > 1 and children[1] and hasattr(children[1], 'data') and children[1].data == 'group_or_list':
            has_accessor = True
            accessor_node = children[1]
            
            # Make the accessor aware of its parent
            accessor_node.parent = node
            
            # Visit to validate the accessor
            self.visit(accessor_node)
        
        # Determine the indices for the assignment operator and expression
        if has_accessor:
            assign_op_idx = 2
            expr_idx = 3
        else:
            assign_op_idx = 1
            expr_idx = 2
        
        # Extract the assignment operator
        assign_op_node = children[assign_op_idx]
        if hasattr(assign_op_node, 'data'):
            # It's a Tree node (e.g., assign_op), extract the token from its children
            op = assign_op_node.children[0].value
        else:
            # It's a token directly
            op = assign_op_node.value if hasattr(assign_op_node, 'value') else '='
        
        # Get the value being assigned
        expr_node = children[expr_idx]
        expr_val = self.visit(expr_node)
        
        # Store the type of expr_val for later reference
        if isinstance(expr_val, tuple) and len(expr_val) >= 2:
            self.variable_types[var_name] = expr_val[0]
        
        # Handle different types of assignments
        if op == '=':
            if isinstance(expr_val, tuple):
                if expr_val[0] == 'text':
                    # For text literals, pass the actual text value, not '='
                    # The key fix is here - directly use the value without using f-strings
                    # which might be causing the issue with quote preservation
                    self.emit('ASSIGN', expr_val[1], None, var_name)
                else:
                    self.emit('ASSIGN', expr_val[1], None, var_name)
            else:
                self.emit('ASSIGN', expr_val, None, var_name)
        else:
            # Handle compound assignments (+=, -=, etc.)
            temp = self.get_temp()
            self.emit('ASSIGN', var_name, None, temp)
            rhs = expr_val[1] if isinstance(expr_val, tuple) else expr_val
            result_temp = self.get_temp()
            
            # Get the types for handling operations
            var_type = self.get_type(var_name)
            expr_type = expr_val[0] if isinstance(expr_val, tuple) else self.get_type(expr_val)
            
            if op == '+=':
                # Special handling for text concatenation
                if var_type == "text" or expr_type == "text":
                    self.emit('CONCAT', temp, rhs, result_temp)
                    self.variable_types[result_temp] = "text"
                else:
                    self.emit('ADD', temp, rhs, result_temp)
                    if var_type == "point" or expr_type == "point" or var_type == "float" or expr_type == "float":
                        self.variable_types[result_temp] = "point"
                    else:
                        self.variable_types[result_temp] = "integer"
            elif op == '-=':
                if var_type == "text" or expr_type == "text":
                    # Error for text subtraction
                    self.emit('ERROR', "Cannot subtract from text", None, result_temp)
                else:
                    self.emit('SUB', temp, rhs, result_temp)
                    if var_type == "point" or expr_type == "point" or var_type == "float" or expr_type == "float":
                        self.variable_types[result_temp] = "point"
                    else:
                        self.variable_types[result_temp] = "integer"
            elif op == '*=':
                if var_type == "text" or expr_type == "text":
                    # Error for text multiplication
                    self.emit('ERROR', "Cannot multiply text", None, result_temp)
                else:
                    self.emit('MUL', temp, rhs, result_temp)
                    if var_type == "point" or expr_type == "point" or var_type == "float" or expr_type == "float":
                        self.variable_types[result_temp] = "point"
                    else:
                        self.variable_types[result_temp] = "integer"
            elif op == '/=':
                if var_type == "text" or expr_type == "text":
                    # Error for text division
                    self.emit('ERROR', "Cannot divide text", None, result_temp)
                else:
                    self.emit('DIV', temp, rhs, result_temp)
                    # Division always results in a point (float)
                    self.variable_types[result_temp] = "point"
            else:
                # fallback
                self.emit('ASSIGN', rhs, None, result_temp)
            
            self.emit('ASSIGN', result_temp, None, var_name)
            # Update the variable type
            if result_temp in self.variable_types:
                self.variable_types[var_name] = self.variable_types[result_temp]
        
        return None

    def visit_show_statement(self, node):
        """
        Generate TAC for show statements, properly handling list indexing in arguments.
        Structure: SHOW LPAREN expression RPAREN
        """
        # Get the expression inside the show() function
        expr = self.visit(node.children[2])
        
        # If expr is a temporary variable (like from LIST_ACCESS), use it directly
        if isinstance(expr, str) and expr.startswith('t'):
            val = expr
        else:
            # Otherwise, extract the value part if it's a tuple
            val = expr[1] if isinstance(expr, tuple) and len(expr) >= 2 else expr
        
        # Emit PRINT instruction with the value
        self.emit('PRINT', val, None, None)
        return None
    
    def visit_func_definition(self, node):
        # function: func identifier(...) { ... }
        func_name = node.children[1].value
        
        # Extract parameter names
        param_names = []
        param_node = node.children[3]
        if hasattr(param_node, 'children'):
            # Multiple parameters
            for child in param_node.children:
                if hasattr(child, 'type') and child.type == 'IDENTIFIER':
                    param_names.append(child.value)
        elif hasattr(param_node, 'type') and param_node.type == 'IDENTIFIER':
            # Single parameter
            param_names.append(param_node.value)
        
        # Create labels for function
        func_label = self.get_label()
        end_label = self.get_label()
        skip_label = self.get_label()
        
        # GOTO skip_label so we don't execute the function body now
        self.emit('GOTO', None, None, skip_label)

        # Mark function start with parameter names
        self.emit('FUNCTION', func_name, param_names, func_label)
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
        target_type = node.children[0].value.lower()
        expr = self.visit(node.children[2])
        temp = self.get_temp()
        
        # Track the type of the result
        self.variable_types[temp] = target_type
        
        # In a real system, you'd have dedicated instructions or a type system
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
        # Generate labels for different parts of the control flow
        else_label = self.get_label()
        end_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', condition, None, else_label)
        
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
        """Generate TAC for else-if statements (recheck)."""
        if not node or not hasattr(node, 'children') or len(node.children) < 5:
            return None
        
        # Generate label for the next else-if part
        next_else_label = self.get_label()
        
        # Evaluate the condition
        condition = self.visit(node.children[2])
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', condition, None, next_else_label)
        
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

    def visit_repeat_statement(self, node):
        """
        Generate TAC for repeat loops (while loops).
        Structure: REPEAT LPAREN expression RPAREN LBRACE loop_block RBRACE
        """
        # Generate simplified labels
        start_label = self.get_label()
        end_label = self.get_label()
        
        # Save these labels for loop control
        self.loop_stack.append((start_label, end_label))
        
        # 1. Loop start (check condition)
        self.emit('LABEL', None, None, start_label)
        
        # 2. Get condition result
        condition = self.visit(node.children[2])
        
        # 3. Exit loop if condition is false
        self.emit('IFFALSE', condition, None, end_label)
        
        # 4. Execute loop body
        self.visit(node.children[4])  # loop_block
        
        # 5. Go back to condition check
        self.emit('GOTO', None, None, start_label)
        
        # 6. Loop exit point
        self.emit('LABEL', None, None, end_label)
        
        # Clean up
        self.loop_stack.pop()
        
        return None

    def visit_do_repeat_statement(self, node):
        """
        Generate TAC for do-repeat loops (do-while loops).
        Structure: DO LBRACE loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        # Generate simplified labels
        start_label = self.get_label()
        cond_label = self.get_label()
        end_label = self.get_label()
        
        # Save these labels for loop control
        self.loop_stack.append((cond_label, end_label))
        
        # 1. Loop start
        self.emit('LABEL', None, None, start_label)
        
        # 2. Execute loop body first (do-while executes at least once)
        self.visit(node.children[2])  # loop_block
        
        # 3. Check condition
        self.emit('LABEL', None, None, cond_label)
        condition = self.visit(node.children[6])
        
        # 4. Go back to start if condition is true
        self.emit('IFTRUE', condition, None, start_label)
        
        # 5. Loop exit point
        self.emit('LABEL', None, None, end_label)
        
        # Clean up
        self.loop_stack.pop()
        
        return None

    def visit_control_flow(self, node):
        """
        Handle exit and next statements within loops.
        """
        stmt_type = node.children[0].value.lower()  # "exit" or "next"
        
        # Require being in a loop context
        if not self.loop_stack:
            # Not in a loop, but we'll still generate code to avoid errors
            return None
        
        # Get the appropriate labels from the current loop
        update_label, end_label = self.loop_stack[-1]
        
        if stmt_type == "exit":
            # Jump to the end of the loop (break)
            self.emit('GOTO', None, None, end_label)
        else:  # next (continue)
            # Jump to the update section of the loop
            # This is important: in a for loop, continue skips the rest of the body
            # but still executes the update expression
            self.emit('GOTO', None, None, update_label)
        
        return None
    
    def visit_each_statement(self, node):
        """
        Generate TAC for each loops (for loops).
        Structure: EACH LPAREN each_initialization expression SEMICOLON (expression | var_assign) RPAREN LBRACE loop_block RBRACE
        """
        # Generate labels for the different parts of the loop
        init_label = self.get_label()  # Initialization
        cond_label = self.get_label()  # Condition check
        body_label = self.get_label()  # Loop body
        update_label = self.get_label()  # Update step
        end_label = self.get_label()    # End of loop
        
        # Save labels for loop control (for exit/next statements)
        # Use update_label for 'next' to skip to the update section
        self.loop_stack.append((update_label, end_label))
        
        # 1. Initialize loop variable
        if len(node.children) > 2 and node.children[2]:
            self.visit(node.children[2])  # each_initialization
        
        # 2. Jump to condition check
        self.emit('GOTO', None, None, cond_label)
        
        # 3. Label for the loop body
        self.emit('LABEL', None, None, body_label)
        
        # 4. Execute loop body
        # Find the loop_block node
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'loop_block':
                self.visit(child)
                loop_body_found = True
                break
        
        # If we couldn't find it by data type, try by position
        if not loop_body_found:
            loop_body_index = 7  # Most likely position based on grammar
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        
        # 5. Label for update step
        self.emit('LABEL', None, None, update_label)
        
        # 6. Process update expression - Enhanced to properly handle increment/decrement
        if len(node.children) > 5 and node.children[5]:
            update_node = node.children[5]
            
            # Check if this is just an id_usage with increment/decrement
            if hasattr(update_node, 'data') and update_node.data == 'id_usage':
                var_name = update_node.children[0].value
                
                # Look for increment/decrement operators in id_usagetail
                for child in update_node.children[1:]:
                    if hasattr(child, 'data') and child.data == 'id_usagetail':
                        for subchild in child.children:
                            if hasattr(subchild, 'data') and subchild.data == 'unary_op':
                                if hasattr(subchild.children[0], 'type'):
                                    op_type = subchild.children[0].type
                                    if op_type == 'INC_OP':  # i++
                                        self.emit('ADD', var_name, 1, var_name)
                                    elif op_type == 'DEC_OP':  # i--
                                        self.emit('SUB', var_name, 1, var_name)
            
            # If it's not a simple increment/decrement, just process normally
            if not (hasattr(update_node, 'data') and update_node.data == 'id_usage'):
                self.visit(update_node)
        
        # 7. Jump back to the condition check
        self.emit('GOTO', None, None, cond_label)
        
        # 8. Label for condition check
        self.emit('LABEL', None, None, cond_label)
        
        # 9. Evaluate condition
        condition_temp = self.visit(node.children[3])
        
        # 10. If condition is true, go to loop body; otherwise exit
        self.emit('IFTRUE', condition_temp, None, body_label)
        
        # 11. Label for loop end
        self.emit('LABEL', None, None, end_label)
        
        # 12. Clean up
        self.loop_stack.pop()
        
        return None

    def visit_repeat_statement(self, node):
        """
        Generate TAC for repeat loops (while loops).
        Structure: REPEAT LPAREN expression RPAREN LBRACE loop_block RBRACE
        """
        # Generate labels
        loop_start = self.get_label()
        loop_end = self.get_label()
        
        # Save labels for control flow
        self.loop_stack.append((loop_start, loop_end))
        
        # 1. Start of loop - condition check
        self.emit('LABEL', None, None, loop_start)
        
        # 2. Evaluate condition fresh for each iteration
        condition_temp = self.visit(node.children[2])
        
        # 3. Exit if condition is false
        self.emit('IFFALSE', condition_temp, None, loop_end)
        
        # 4. Execute loop body
        # Find the loop body node
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'loop_block':
                self.visit(child)
                loop_body_found = True
                break
        
        # If we couldn't find it by data type, try by position
        if not loop_body_found:
            loop_body_index = 4  # Most likely position based on grammar
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        
        # 5. Jump back to start for next iteration
        self.emit('GOTO', None, None, loop_start)
        
        # 6. Loop exit point
        self.emit('LABEL', None, None, loop_end)
        
        # Clean up
        self.loop_stack.pop()
        
        return None

    def visit_do_repeat_statement(self, node):
        """
        Generate TAC for do-repeat loops (do-while loops).
        Structure: DO LBRACE loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        # Generate labels
        loop_start = self.get_label()
        loop_cond = self.get_label()
        loop_end = self.get_label()
        
        # Save labels for control flow
        self.loop_stack.append((loop_start, loop_end))
        
        # 1. Start of loop
        self.emit('LABEL', None, None, loop_start)
        
        # 2. Execute loop body
        # Find the loop body node
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'loop_block':
                self.visit(child)
                loop_body_found = True
                break
        
        # If we couldn't find it by data type, try by position
        if not loop_body_found:
            loop_body_index = 2  # Most likely position based on grammar
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        
        # 3. Condition check label
        self.emit('LABEL', None, None, loop_cond)
        
        # 4. Evaluate condition - must be fresh each iteration
        condition_node_index = 6  # Expected position of condition expression
        condition_temp = self.visit(node.children[condition_node_index])
        
        # 5. Go back to start if condition is true
        self.emit('IFTRUE', condition_temp, None, loop_start)
        
        # 6. Exit point
        self.emit('LABEL', None, None, loop_end)
        
        # Clean up
        self.loop_stack.pop()
        
        return None
    
    def visit_each_func_statement(self, node):
        """
        Generate TAC for each loops within functions.
        Structure: EACH LPAREN each_initialization expression SEMICOLON (expression | var_assign) RPAREN LBRACE func_loop_block RBRACE
        """
        # Generate labels
        init_label = self.get_label()
        cond_label = self.get_label()
        body_label = self.get_label()
        update_label = self.get_label()
        end_label = self.get_label()
        
        # Save labels for control flow
        self.loop_stack.append((update_label, end_label))
        
        # 1. Label for initialization
        self.emit('LABEL', None, None, init_label)
        
        # 2. Initialize loop variable
        self.visit(node.children[2])  # each_initialization
        
        # 3. Jump to condition check
        self.emit('GOTO', None, None, cond_label)
        
        # 4. Label for the loop body
        self.emit('LABEL', None, None, body_label)
        
        # 5. Execute loop body
        # Find the func_loop_block node
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'func_loop_block':
                self.visit(child)
                loop_body_found = True
                break
        
        # If we couldn't find it by data type, try by position
        if not loop_body_found:
            loop_body_index = 7  # Most likely position based on grammar
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        
        # 6. Label for update step
        self.emit('LABEL', None, None, update_label)
        
        # 7. Execute update expression
        self.visit(node.children[5])  # update expression
        
        # 8. Jump back to condition check
        self.emit('GOTO', None, None, cond_label)
        
        # 9. Label for condition check
        self.emit('LABEL', None, None, cond_label)
        
        # 10. Evaluate condition - CRITICAL: This must happen at the start of EACH iteration
        # Visit the condition node to generate its evaluation code
        condition_temp = self.visit(node.children[3])
        
        # 11. If condition is true, go to loop body; otherwise exit
        self.emit('IFTRUE', condition_temp, None, body_label)
        self.emit('GOTO', None, None, end_label)  # Exit if condition is false
        
        # 12. Label for loop end
        self.emit('LABEL', None, None, end_label)
        
        # Clean up
        self.loop_stack.pop()
        
        return None

    def visit_repeat_func_statement(self, node):
        """
        Generate TAC for repeat loops within functions.
        Structure: REPEAT LPAREN expression RPAREN LBRACE func_loop_block RBRACE
        """
        # Generate labels
        loop_start = self.get_label()
        loop_end = self.get_label()
        
        # Save labels for control flow
        self.loop_stack.append((loop_start, loop_end))
        
        # 1. Start of loop - condition check
        self.emit('LABEL', None, None, loop_start)
        
        # 2. Evaluate condition fresh for each iteration
        condition_temp = self.visit(node.children[2])
        
        # 3. Exit if condition is false
        self.emit('IFFALSE', condition_temp, None, loop_end)
        
        # 4. Execute loop body
        # Find the func_loop_block node
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'func_loop_block':
                self.visit(child)
                loop_body_found = True
                break
        
        # If we couldn't find it by data type, try by position
        if not loop_body_found:
            loop_body_index = 4  # Most likely position based on grammar
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        
        # 5. Jump back to start for next iteration
        self.emit('GOTO', None, None, loop_start)
        
        # 6. Loop exit point
        self.emit('LABEL', None, None, loop_end)
        
        # Clean up
        self.loop_stack.pop()
        
        return None

    def visit_do_repeat_func_statement(self, node):
        """
        Generate TAC for do-repeat loops within functions.
        Structure: DO LBRACE func_loop_block RBRACE REPEAT LPAREN expression RPAREN
        """
        # Generate labels
        loop_start = self.get_label()
        loop_cond = self.get_label()
        loop_end = self.get_label()
        
        # Save labels for control flow
        self.loop_stack.append((loop_start, loop_end))
        
        # 1. Start of loop
        self.emit('LABEL', None, None, loop_start)
        
        # 2. Execute loop body
        # Find the func_loop_block node
        loop_body_found = False
        for i, child in enumerate(node.children):
            if hasattr(child, 'data') and child.data == 'func_loop_block':
                self.visit(child)
                loop_body_found = True
                break
        
        # If we couldn't find it by data type, try by position
        if not loop_body_found:
            loop_body_index = 2  # Most likely position based on grammar
            if len(node.children) > loop_body_index:
                self.visit(node.children[loop_body_index])
        
        # 3. Condition check label
        self.emit('LABEL', None, None, loop_cond)
        
        # 4. Evaluate condition - must be fresh each iteration
        condition_node_index = 6  # Expected position of condition expression
        condition_temp = self.visit(node.children[condition_node_index])
        
        # 5. Go back to start if condition is true
        self.emit('IFTRUE', condition_temp, None, loop_start)
        
        # 6. Exit point
        self.emit('LABEL', None, None, loop_end)
        
        # Clean up
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
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', condition, None, else_label)
        
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
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', condition, None, next_else_label)
        
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

    def visit_switch_statement(self, node):
        """
        Generate TAC for switch statements.
        Structure: SWITCH LPAREN expression RPAREN LBRACE CASE literals COLON program case_tail default RBRACE
        """
        # Generate label for the end of the switch statement
        end_label = self.get_label()
        
        # Evaluate the switch expression
        switch_expr = self.visit(node.children[2])
        
        # Generate code for the first case
        case_value = self.visit(node.children[6])
        
        # Compare switch expression with case value
        comp_temp = self.get_temp()
        self.emit('EQ', switch_expr, case_value[1] if isinstance(case_value, tuple) else case_value, comp_temp)
        
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
            self.visit_case_tail(node.children[9], switch_expr, end_label)
        
        # Visit default if present
        if len(node.children) > 10 and node.children[10]:
            self.visit(node.children[10])
        
        # Label for the end of the switch statement
        self.emit('LABEL', None, None, end_label)
        
        return None

    def visit_case_tail(self, node, switch_expr, end_label):
        """
        Generate TAC for additional cases in a switch statement.
        """
        if not node or not hasattr(node, 'children') or len(node.children) < 4:
            return None
        
        # Get the case value
        case_value = self.visit(node.children[1])
        
        # Compare switch expression with case value
        comp_temp = self.get_temp()
        self.emit('EQ', switch_expr, case_value[1] if isinstance(case_value, tuple) else case_value, comp_temp)
        
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
            self.visit_case_tail(node.children[4], switch_expr, end_label)
        
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
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', condition, None, else_label)
        
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
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', condition, None, next_else_label)
        
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
        
        # Generate branch instruction - if condition is false, skip to else block
        self.emit('IFFALSE', condition, None, else_label)
        
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
        
        # Generate branch instruction - if condition is false, skip to next else block
        self.emit('IFFALSE', condition, None, next_else_label)
        
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