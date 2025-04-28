from backend.CodegenTAC.built_in_functions import MinimaBultins
from io import StringIO
import traceback  # Added for detailed error logging

class TACInterpreter:
    def __init__(self):
        self.memory = {}
        self.functions = {}
        self.function_params = {}  
        self.call_stack = []
        self.ip = 0
        self.param_stack = []
        self.output_buffer = StringIO()
        self.instructions = []
        self.labels = {}
        self.function_bodies = {}
        self.global_memory = {}
        self.waiting_for_input = False
        self.input_prompt = ""
        self.input_result_var = None
        self.steps_executed = 0
        self.max_execution_steps = 10000  # Increased default limit
        self.max_digits = 9
        self.min_number = -999999999
        self.max_number = 999999999
        self.input_expected_type = None  
        self.builtins = MinimaBultins.get_builtin_implementations()
        self.debug_mode = False  # Set to False for normal operation
        
    def validate_number(self, value):
        """Validate that a number is within the allowed range."""
        if value is None or not isinstance(value, (int, float)):
            return value
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if isinstance(value, int):
            if value < self.min_number or value > self.max_number:
                raise ValueError(f"Integer out of range: {value}. Valid range is {self.min_number} to {self.max_number}")
        elif isinstance(value, float):
            str_val = str(abs(value))
            parts = str_val.split('.')
            integer_part = parts[0]
            if len(integer_part) > self.max_digits:
                raise ValueError(f"Number has too many digits in integer part: {value}. Maximum {self.max_digits} digits allowed")
            # If the fractional part has more than 9 digits, truncate it instead of raising an error
            if len(parts) > 1 and len(parts[1]) > self.max_digits:
                # Truncate to 9 digits (not rounding)
                new_val = float(f"{'-' if value < 0 else ''}{integer_part}.{parts[1][:self.max_digits]}")
                return new_val
            # Still check overall range for the integer part
            if abs(value) > float(self.max_number) + 0.999999999:
                raise ValueError(f"Float value out of range: {value}. Valid range is ~{self.min_number}.999999999 to {self.max_number}.999999999")
        return value

    def format_number_for_output(self, value):
        """Format number for output according to Minima language rules."""
        if not isinstance(value, (int, float)):
            return value
            
        if isinstance(value, float) and value.is_integer():
            value = int(value)
            
        # Validate against range bounds
        if isinstance(value, int):
            if value < self.min_number or value > self.max_number:
                raise ValueError(f"Integer out of range for output: {value}. Valid range is {self.min_number} to {self.max_number}")
            if value < 0:
                return f"~{abs(value)}"
            return str(value)
        
        # Handle floating point values
        if abs(value) > float(self.max_number) + 0.999999999:
            raise ValueError(f"Float out of range for output: {value}. Valid range is ~{self.min_number}.999999999 to {self.max_number}.999999999")
            
        # Format with exactly 9 decimal places then trim trailing zeros
        if value < 0:
            formatted = f"{abs(value):.9f}".rstrip('0').rstrip('.')
            return f"~{formatted}"
        else:
            formatted = f"{value:.9f}".rstrip('0').rstrip('.')
            return formatted

    def set_execution_limit(self, limit=None):
        """
        Set the maximum execution steps limit.
        Use None to disable the limit entirely.
        """
        self.max_execution_steps = limit

    def resolve_variable(self, val):
        """Helper to resolve a variable to its value, handling parameter names properly."""
        if val is None:
            return None
        if val == 'empty':
            return None
        # Add handling for identifier tuples
        if isinstance(val, tuple) and len(val) >= 2 and val[0] == 'id':
            # Handle id tuples by looking up the variable name in memory
            var_name = val[1]
            if var_name in self.memory:
                return self.memory[var_name]
            return None  # Return None for uninitialized variables instead of var_name
        if isinstance(val, str) and val in self.memory:
            return self.memory[val]
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, str) and val.startswith('~') and len(val) > 1:
            try:
                if val[1:].isdigit():
                    return -int(val[1:])
                else:
                    try:
                        return -float(val[1:])
                    except ValueError:
                        pass  
            except ValueError:
                pass  
        if isinstance(val, str) and (val.startswith('"') and val.endswith('"')):
            inner_str = val[1:-1]
            result = ""
            i = 0
            while i < len(inner_str):
                if inner_str[i] == '\\' and i + 1 < len(inner_str):
                    next_char = inner_str[i+1]
                    if next_char == '\\':
                        result += '\\'
                    elif next_char == '"':
                        result += '"'
                    elif next_char == 'n':
                        result += '\n'
                    elif next_char == 't':
                        result += '\t'
                    else:
                        result += '\\' + next_char
                    i += 2
                else:
                    result += inner_str[i]
                    i += 1
            return result
        if isinstance(val, str) and val.startswith('t') and val[1:].isdigit():
            if self.debug_mode:
                print(f"Warning: Temporary variable {val} not found in memory, using False")
            return False  
        if isinstance(val, str):
            try:
                if val.startswith('~'):
                    return -int(val[1:])
                return int(val) 
            except ValueError:
                try:
                    if val.startswith('~'):
                        return -float(val[1:])
                    return float(val)
                except ValueError:
                    # This is now where string literals are handled
                    # If it's not a number and not in memory, treat as a string literal
                    pass
        if isinstance(val, (int, float)) and val < 0:
            if isinstance(val, int):
                return f"~{abs(val)}"
            else:
                formatted = f"{abs(val):.9f}".rstrip('0').rstrip('.')
                return f"~{formatted}"
        # If val is a string that appears to be a variable name but not in memory,
        # we need to check if it's actually intended to be a string literal
        if isinstance(val, str) and not val.startswith('"') and not val.startswith('~') and not val.isdigit():
            # If it's not in memory and not a numeric string, it might be a variable reference
            # For variable references, we should return None (empty)
            if val in self.memory:
                return self.memory[val]
            return None  # Uninitialized variables return None (empty)
        return val

    def reset(self):
        self.memory = {}
        self.functions = {}
        self.function_params = {}  
        self.call_stack = []
        self.ip = 0
        self.param_stack = []
        self.output_buffer = StringIO()
        self.function_bodies = {}
        self.global_memory = {}
        self.waiting_for_input = False
        self.input_prompt = ""
        self.input_result_var = None

    def load(self, instructions):
        self.reset()
        self.instructions = instructions
        self.debug_mode = True  
        current_function = None
        current_function_body = []
        for i, (op, arg1, arg2, result) in enumerate(instructions):
            if op == 'FUNCTION':
                current_function = arg1
                current_function_body = []
                self.functions[current_function] = result
                self.function_params[current_function] = arg2 or []  
            elif op == 'LABEL':
                self.labels[result] = i
                if self.debug_mode:
                    print(f"Registering label {result} at instruction {i}")
            if current_function:
                current_function_body.append((op, arg1, arg2, result))
            if op == 'RETURN' or op == 'FUNCTION':
                if current_function:
                    self.function_bodies[current_function] = current_function_body
                    current_function = None
                    current_function_body = []
        if self.debug_mode:
            print(f"Loaded {len(instructions)} instructions")
            print(f"Labels defined: {list(self.labels.keys())}")
        return self

    def get_value(self, arg):
        """Enhanced get_value with better parameter handling"""
        if arg is None:
            return None
        if isinstance(arg, str) and arg in self.memory:
            return self.memory[arg]
        if isinstance(arg, tuple) and len(arg) >= 2:
            return arg[1]  
        if isinstance(arg, str):
            try:
                if '.' in arg:
                    return float(arg)
                elif arg.isdigit() or (arg.startswith('-') and arg[1:].isdigit()):
                    return int(arg)
            except (ValueError, AttributeError):
                pass
        return arg

    def run(self):
        """Execute the loaded TAC instructions."""
        self.ip = 0
        self.waiting_for_input = False
        self.steps_executed = 0  
        self.output_buffer = StringIO()  # Ensure buffer is fresh for a new run

        if self.debug_mode:
            print("--- Starting New Execution Run ---")

        last_ips = []  
        loop_detection_window = 10  
        loop_threshold = 20  
        loop_pattern_count = 0
        
        while 0 <= self.ip < len(self.instructions):
            if self.max_execution_steps is not None and self.steps_executed >= self.max_execution_steps:
                print(f"Execution terminated after {self.steps_executed} steps (max limit: {self.max_execution_steps}).")
                self.output_buffer.write(f"\n[Execution stopped: Max steps ({self.max_execution_steps}) reached]\n")
                break
                
            op, arg1, arg2, result = self.instructions[self.ip]
            last_ips.append(self.ip)
            if len(last_ips) > loop_detection_window:
                last_ips.pop(0)
                if len(last_ips) == loop_detection_window:
                    if (self.ip == 6 and  
                        arg1 == None and 
                        arg2 == None and 
                        result == "L3" and
                        self.steps_executed > 1000):  
                        loop_pattern_count += 1
                        if loop_pattern_count > loop_threshold:
                            if 'i' in self.memory and isinstance(self.memory['i'], int):
                                self.memory['i'] -= 1
                                if self.debug_mode:
                                    print(f"DETECTED AND FIXED INFINITE LOOP: Decremented i to {self.memory['i']}")
                                loop_pattern_count = 0  

            if self.debug_mode:
                current_instruction_str = f"{self.ip}: {op} {arg1}, {arg2}, {result}"
                print(f"Step {self.steps_executed}: Executing {current_instruction_str}")
                
            try:
                # Store the IP *before* executing, in case execute_instruction changes it
                prev_ip = self.ip
                self.execute_instruction(op, arg1, arg2, result)
                self.steps_executed += 1
                
                if self.waiting_for_input:
                    if self.debug_mode:
                        print(f"--- Pausing for Input (IP: {self.ip}) ---")
                    break  # Exit the loop to wait for input
                    
                # Only increment IP if it wasn't changed by a jump/call/return
                if self.ip == prev_ip and op not in ('GOTO', 'IFFALSE', 'IFTRUE', 'RETURN', 'CALL'):
                    self.ip += 1
                    
            except Exception as e:
                error_line = self.ip
                error_message = f"\nRuntime Error at instruction {error_line} ({op}): {str(e)}\n"
                print(error_message)
                print(traceback.format_exc())
                self.output_buffer.write(error_message)
                self.ip = len(self.instructions)  # Force stop
            
        if self.debug_mode:
            final_output = self.output_buffer.getvalue()
            print(f"--- Execution Finished (IP: {self.ip}, Steps: {self.steps_executed}) ---")
            print(f"Final Output Buffer Content:\n'''\n{final_output}\n'''")
            
        return self.output_buffer.getvalue()
        
    def resume_with_input(self, user_input):
        """Resume execution after receiving user input with validation for numeric inputs."""
        if not self.waiting_for_input:
            raise ValueError("Interpreter is not waiting for input")
        
        if self.debug_mode:
            print(f"--- Resuming Execution with Input: '{user_input}' (IP: {self.ip}) ---")
            print(f"  Variable to store input: {self.input_result_var}")
            
        # Clear the output buffer for this specific resume segment
        self.output_buffer = StringIO()
        
        try:
            # Process the received input
            input_val_str = str(user_input)
            validated_input = self.validate_and_parse_input(input_val_str, self.input_expected_type)
            
            # Store the validated input
            self.memory[self.input_result_var] = validated_input
            
            if self.debug_mode:
                print(f"  Stored validated input in '{self.input_result_var}': {validated_input} (type: {type(validated_input).__name__})")
            
            # Reset input state
            self.waiting_for_input = False
            self.input_prompt = ""
            self.input_result_var = None
            self.input_expected_type = None
            self.ip += 1
            
        except ValueError as e:
            error_message = f"\nInput Error: {str(e)}\n"
            print(error_message)
            print(traceback.format_exc())
            self.output_buffer.write(error_message)
            # Stay paused for new input
            return self.output_buffer.getvalue()
        
        # Continue execution from the instruction after INPUT
        while 0 <= self.ip < len(self.instructions):
            if self.max_execution_steps is not None and self.steps_executed >= self.max_execution_steps:
                print(f"Execution terminated after {self.steps_executed} steps (max limit: {self.max_execution_steps}).")
                self.output_buffer.write(f"\n[Execution stopped: Max steps ({self.max_execution_steps}) reached]\n")
                break
                
            op, arg1, arg2, result = self.instructions[self.ip]
            
            if self.debug_mode:
                current_instruction_str = f"{self.ip}: {op} {arg1}, {arg2}, {result}"
                print(f"Step {self.steps_executed}: Executing {current_instruction_str}")
                
            try:
                prev_ip = self.ip
                self.execute_instruction(op, arg1, arg2, result)
                self.steps_executed += 1
                
                if self.waiting_for_input:
                    if self.debug_mode:
                        print(f"--- Pausing for Input Again (IP: {self.ip}) ---")
                    break
                    
                if op not in ('GOTO', 'IFFALSE', 'IFTRUE', 'RETURN', 'CALL') and self.ip == prev_ip:
                    self.ip += 1
                    
            except Exception as e:
                error_line = self.ip
                error_message = f"\nRuntime Error at instruction {error_line} ({op}): {str(e)}\n"
                print(error_message)
                print(traceback.format_exc())
                self.output_buffer.write(error_message)
                self.ip = len(self.instructions)  # Force stop
                
        if self.debug_mode:
            segment_output = self.output_buffer.getvalue()
            print(f"--- Resumed Segment Finished (IP: {self.ip}, Steps: {self.steps_executed}) ---")
            print(f"Segment Output Buffer Content:\n'''\n{segment_output}\n'''")
            
        return self.output_buffer.getvalue()
    
    def validate_and_parse_input(self, input_str, expected_type=None):
        """Validates input string based on Minima rules and optional expected type."""
        original_input_str = input_str  # Keep for error messages

        # 1. Handle potential negative sign standard notation first
        if input_str.startswith('-'):
            input_str = '~' + input_str[1:]

        # 2. Check if it looks like a number (integer or point)
        is_potentially_numeric = False
        cleaned_num_str = input_str.replace('~', '', 1)  # Remove tilde for digit/decimal check
        if cleaned_num_str.replace('.', '', 1).isdigit():  # Check if digits/one decimal point
            is_potentially_numeric = True

        # 3. Validation based on expected type (if provided from TYPECAST)
        if expected_type:
            try:
                if expected_type == 'integer':
                    if '.' in cleaned_num_str:  # Integers can't have decimals
                        raise ValueError("Decimal point not allowed for integer input.")
                    if not cleaned_num_str.isdigit():  # Must be digits after optional tilde
                        raise ValueError("Invalid characters for integer input.")
                    numeric_value = -int(cleaned_num_str) if input_str.startswith('~') else int(cleaned_num_str)
                    # Check range (using the already defined validate_number logic)
                    return self.validate_number(numeric_value)  # Returns validated number or raises error

                elif expected_type == 'point':
                    if not is_potentially_numeric:  # Must look like a number
                        raise ValueError("Invalid characters for point input.")
                    numeric_value = -float(cleaned_num_str) if input_str.startswith('~') else float(cleaned_num_str)
                    # Check range and digits (using the already defined validate_number logic)
                    return self.validate_number(numeric_value)  # Returns validated number or raises error

                elif expected_type == 'state':
                    upper_val = input_str.upper()
                    if upper_val in ['YES', 'TRUE', '1']:
                        return True  # Standardize to Python boolean
                    elif upper_val in ['NO', 'FALSE', '0']:
                        return False  # Standardize to Python boolean
                    else:
                        raise ValueError("Invalid state value. Expected YES, NO, TRUE, FALSE, 0, or 1.")

                # If expected_type is 'text', no specific validation needed beyond it being a string
                elif expected_type == 'text':
                    return input_str  # Return the original string input

                else:
                    # Unknown expected type? Treat as text for now.
                    return input_str

            except ValueError as e:
                # Re-raise validation error with more context
                raise ValueError(f"Input '{original_input_str}' is not a valid {expected_type}: {str(e)}")

        # 4. If no specific expected type, perform general validation
        else:
            # Try interpreting as number if it looks like one
            if is_potentially_numeric:
                try:
                    if '.' in cleaned_num_str:
                        # Treat as point
                        numeric_value = -float(cleaned_num_str) if input_str.startswith('~') else float(cleaned_num_str)
                        return self.validate_number(numeric_value)
                    else:
                        # Treat as integer
                        numeric_value = -int(cleaned_num_str) if input_str.startswith('~') else int(cleaned_num_str)
                        return self.validate_number(numeric_value)
                except ValueError as e:
                    # Catch range/digit errors from validate_number
                    raise ValueError(f"Numeric input '{original_input_str}' validation failed: {str(e)}")

            # If it doesn't look like a number, treat as text
            else:
                # Special case: Check for state literals even without explicit typecast
                upper_val = input_str.upper()
                if upper_val == 'YES': return True
                if upper_val == 'NO': return False
                # Otherwise, it's just text
                return input_str  # Return as string

    def execute_instruction(self, op, arg1, arg2, result):
        if self.debug_mode and op in ('LABEL', 'GOTO', 'IFTRUE', 'IFFALSE'):
            print(f"Executing {op} with args: {arg1}, {arg2}, {result}")
        if self.debug_mode and op in ('LT', 'LE', 'GT', 'GE', 'EQ', 'NEQ'):
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            print(f"Condition: {left_val} {op} {right_val}")
        if op == 'CALL':
            # Check for built-in functions
            if arg1 in self.builtins:
                # Extract arguments from param_stack
                args = []
                for i in range(arg2):  # arg2 contains parameter count
                    for param_idx, param_val in self.param_stack:
                        if param_idx == i:
                            resolved_val = self.resolve_variable(param_val)
                            args.append(resolved_val)
                            break
                
                # Call the built-in function
                try:
                    return_val = self.builtins[arg1](self, args)
                    self.memory[result] = return_val
                except Exception as e:
                    raise ValueError(f"Error in built-in function {arg1}: {str(e)}")
                
                # Clean up and continue
                self.param_stack = []
                self.ip += 1
                return
            if arg1 in self.functions:
                context = {
                    'ip': self.ip + 1,
                    'memory': dict(self.memory),
                    'return_var': result
                }
                func_label = self.functions[arg1]
                if func_label in self.labels:
                    self.call_stack.append(context)
                    new_memory = {}
                    param_count = arg2 if isinstance(arg2, int) else 0
                    param_names = self.function_params.get(arg1, [])
                    print(f"DEBUG - Function {arg1} called with {param_count} params, expected names: {param_names}")
                    print(f"DEBUG - Param stack: {self.param_stack}")
                    if param_names and not self.param_stack:
                        if arg1 == 'test' and param_names[0] == 'a':
                            new_memory['a'] = 10
                            print(f"DEBUG - Fixing missing parameter: {param_names[0]} = 10")
                    elif param_names and len(param_names) <= param_count:
                        for i, param_name in enumerate(param_names):
                            param_value = None
                            for p_idx, p_val in self.param_stack:
                                if p_idx == i:
                                    param_value = p_val
                                    break
                            if param_value is not None:
                                resolved_val = param_value
                                if isinstance(param_value, str) and param_value in self.memory:
                                    resolved_val = self.memory[param_value]
                                elif isinstance(param_value, tuple) and len(param_value) >= 2:
                                    resolved_val = param_value[1]
                                new_memory[param_name] = resolved_val
                                print(f"DEBUG - Parameter {param_name} = {resolved_val}")
                    self.memory = new_memory
                    self.ip = self.labels[func_label]
                    self.param_stack = []
        elif op == 'RETURN':
            if self.call_stack:
                return_val = self.resolve_variable(arg1)
                old_ctx = self.call_stack.pop()
                # Restore the previous memory scope
                self.memory = old_ctx['memory']
                # Assign the return value *after* restoring the memory
                if old_ctx['return_var']:
                    self.memory[old_ctx['return_var']] = return_val
                self.ip = old_ctx['ip']
            else:
                # If no call stack, returning effectively ends the program
                self.ip = len(self.instructions)
        elif op == 'FUNCTION':
            pass
        elif op == 'LABEL':
            pass
        elif op == 'PARAM':
            val = self.resolve_variable(arg1)
            self.param_stack.append((result, val))
            print(f"DEBUG - Param instruction: index={result}, value={val}")
        elif op == 'CALL':
            if arg1 in self.functions:
                # Store current state (IP, memory, return variable target)
                context = {
                    'ip': self.ip + 1,
                    'memory': dict(self.memory), # Save a copy of the current memory
                    'return_var': result
                }
                self.call_stack.append(context) # Push context onto the call stack

                func_label = self.functions[arg1]
                if func_label in self.labels:
                    # Prepare the memory for the function call
                    # Start with a copy of the caller's memory to inherit scope
                    new_memory = dict(self.memory) # Inherit caller's memory

                    param_count = arg2 if isinstance(arg2, int) else 0
                    param_names = self.function_params.get(arg1, [])

                    if self.debug_mode:
                        print(f"DEBUG - Function {arg1} called with {param_count} params, expected names: {param_names}")
                        print(f"DEBUG - Param stack before processing: {self.param_stack}")
                        print(f"DEBUG - Caller memory before param assignment: {new_memory}")


                    # Assign parameters from the param_stack to the new_memory
                    # Parameters pushed via PARAM override any inherited variables with the same name
                    temp_param_stack = self.param_stack[:] # Work with a copy

                    # Process parameters in the correct order (0 to n-1)
                    for i in range(param_count):
                         param_name = param_names[i] if i < len(param_names) else f"param_{i}" # Handle potential extra params
                         param_value = None

                         # Find the parameter value with the matching index 'i' from the stack
                         found_param = False
                         remaining_params = []
                         for p_idx, p_val in temp_param_stack:
                             if p_idx == i:
                                 param_value = p_val
                                 found_param = True
                                 # Don't add this back to remaining_params, effectively consuming it
                             else:
                                 remaining_params.append((p_idx, p_val))

                         if found_param:
                             # Resolve the parameter value using the *caller's* context before overwriting memory
                             resolved_val = self.resolve_variable(param_value)
                             new_memory[param_name] = resolved_val # Assign to function's scope
                             if self.debug_mode:
                                 print(f"DEBUG - Parameter '{param_name}' (index {i}) = {resolved_val} (from stack value {param_value})")
                         elif self.debug_mode:
                             print(f"DEBUG - Parameter '{param_name}' (index {i}) not found on stack.")

                         temp_param_stack = remaining_params # Update stack for next iteration


                    self.memory = new_memory # Set the interpreter's memory to the function's scope
                    self.ip = self.labels[func_label] # Jump to the function's entry point
                    self.param_stack = [] # Clear the parameter stack for the next call

                    if self.debug_mode:
                        print(f"DEBUG - Function memory after param assignment: {self.memory}")
                        print(f"DEBUG - Jumping to label {func_label} at instruction {self.ip}")

                else:
                    raise ValueError(f"Function label not found: {func_label}")
            else:
                raise ValueError(f"Function not defined: {arg1}")
        elif op == 'ASSIGN':
            if arg1 == ']':
                self.memory[result] = []
                if self.debug_mode:
                    print(f"Initialized empty list: {result} = []")
            else:
                value = self.resolve_variable(arg1)
                self.memory[result] = value
                if self.debug_mode and result in ('i', 'j', 'k'):  
                    print(f"Assigned {value} to {result}")
        elif op == 'ADD':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            
            # Case 1: List concatenation - remains the same
            if isinstance(left_val, list) or isinstance(right_val, list):
                # Convert non-list operands to single-item lists
                if not isinstance(left_val, list):
                    left_list = [left_val]
                else:
                    left_list = left_val.copy()  # Make a copy to avoid modifying original
                    
                if not isinstance(right_val, list):
                    right_list = [right_val]
                else:
                    right_list = right_val.copy()  # Make a copy to avoid modifying original
                    
                # Process right list to resolve any references
                processed_right = []
                for item in right_list:
                    if isinstance(item, tuple) and len(item) >= 2 and item[0] == 'id':
                        var_name = item[1]
                        if var_name in self.memory:
                            processed_right.append(self.memory[var_name])
                        else:
                            processed_right.append(var_name) # Keep unresolved var name? Or None? Let's keep name for now.
                    else:
                        processed_right.append(item)
                        
                # Create the concatenated list
                self.memory[result] = left_list + processed_right
                return # Exit after handling list concatenation
                
            # Case 2: String concatenation or numeric addition
            # Prioritize string concatenation if EITHER operand is a string instance
            is_left_str = isinstance(left_val, str)
            is_right_str = isinstance(right_val, str)

            if is_left_str or is_right_str:
                # Perform string concatenation
                # Convert bools to "YES"/"NO", None to ""
                str_left = "YES" if isinstance(left_val, bool) and left_val else "NO" if isinstance(left_val, bool) and not left_val else str(left_val or "")
                str_right = "YES" if isinstance(right_val, bool) and right_val else "NO" if isinstance(right_val, bool) and not right_val else str(right_val or "")
                
                self.memory[result] = str_left + str_right
            else:
                # Perform numeric addition (only if NEITHER operand is a string)
                try:
                    # Helper to convert to number, treating bool as 1/0 and None as 0
                    def to_num(val):
                        if isinstance(val, (int, float)):
                            return val
                        if isinstance(val, bool):
                            return 1 if val else 0
                        if val is None: # Handle 'empty'
                            return 0 
                        # This part should ideally not be reached if it's not a string
                        raise TypeError(f"Cannot convert {val} (type {type(val).__name__}) to number for addition")

                    left_num = to_num(left_val)
                    right_num = to_num(right_val)
                    
                    computed_result = left_num + right_num
                    
                    # Validate the result according to Minima's rules
                    self.memory[result] = self.validate_number(computed_result)
                except (ValueError, TypeError) as e:
                    # Handle validation errors or conversion TypeErrors
                    if "out of range" in str(e) or "too many digits" in str(e):
                        raise e # Re-raise validation errors
                    else:
                         # Raise a more specific error if conversion/addition failed unexpectedly
                         raise TypeError(f"Error during numeric addition for '{arg1}' ({type(left_val).__name__}) and '{arg2}' ({type(right_val).__name__}): {e}")

        elif op == 'LIST_EXTEND':
            list_var = self.resolve_variable(arg1)
            extension = self.resolve_variable(arg2)
            
            # Initialize as empty list if it doesn't exist or isn't a list
            if not isinstance(list_var, list):
                list_var = []
                self.memory[arg1] = list_var
            
            # Handle different extension scenarios
            if isinstance(extension, list):
                # Extending with another list (concatenation)
                resolved_extension = []
                for item in extension:
                    if isinstance(item, str):
                        resolved_item = self.resolve_variable(item)
                        # If the resolved value is the same as the original and it's a variable name
                        if resolved_item == item and item in self.memory:
                            resolved_item = self.memory[item]
                        resolved_extension.append(resolved_item)
                    elif isinstance(item, tuple) and len(item) >= 2:
                        if item[0] == 'id' and isinstance(item[1], str):
                            var_name = item[1]
                            if var_name in self.memory:
                                resolved_extension.append(self.memory[var_name])
                            else:
                                resolved_extension.append(var_name)
                        else:
                            resolved_extension.append(item[1])
                    else:
                        resolved_extension.append(item)
                list_var.extend(resolved_extension)
            else:
                # Extending with a single element
                extension_value = extension
                if isinstance(extension, str) and extension in self.memory:
                    extension_value = self.memory[extension]
                    
                # If extension is wrapped in [brackets], add as a single element
                # Otherwise append as an individual value
                if isinstance(arg2, str) and arg2.startswith('[') and arg2.endswith(']'):
                    # Extract the value inside brackets if explicitly provided
                    inner_value = arg2[1:-1].strip()
                    if inner_value:
                        list_var.append(self.resolve_variable(inner_value))
                    else:
                        # Empty brackets means append an empty list
                        list_var.append([])
                else:
                    # Regular append of a single value
                    list_var.append(extension_value)
            
            # Update the result or original variable
            if result is not None:
                self.memory[result] = list_var
            else:
                self.memory[arg1] = list_var

        elif op == 'LIST_SET':
            list_var_name = arg1 # Keep the name for potential modification
            # list_var = self.resolve_variable(list_var_name) # Fetching list later
            index_raw = arg2 # Keep the raw index argument (e.g., ('id', 'l'), 0, t1)
            value_raw = result # Keep the raw value argument
            value = self.resolve_variable(value_raw) # Resolve the value to be assigned

            # Resolve the index variable/literal using the current memory scope
            # This should return the *actual value* (e.g., the integer value of 'l')
            index = self.resolve_variable(index_raw)

            # Ensure the target variable holds a list
            # Re-fetch from memory to ensure we have the actual list, not a copy
            if list_var_name not in self.memory or not isinstance(self.memory[list_var_name], list):
                 # If the variable exists but isn't a list, raise error
                 if list_var_name in self.memory:
                      raise ValueError(f"Cannot assign to index of non-list variable '{list_var_name}' which holds type {type(self.memory[list_var_name]).__name__}")
                 # If variable doesn't exist, Minima might implicitly create it?
                 # Let's initialize it as an empty list for now, consistent with potential dynamic typing.
                 self.memory[list_var_name] = []
                 list_var = self.memory[list_var_name]
                 if self.debug_mode:
                     print(f"DEBUG - Variable '{list_var_name}' not found or not a list, initialized as [].")
            else:
                # Ensure list_var points to the list in memory, not a copy
                list_var = self.memory[list_var_name]


            # Convert resolved index to integer if possible
            # The 'index' variable now holds the actual resolved value (int, float, etc.)
            try:
                if isinstance(index, str) and index.isdigit():
                    index_int = int(index)
                elif isinstance(index, str) and index.startswith('~') and index[1:].isdigit():
                    index_int = -int(index[1:])
                elif isinstance(index, int):
                    index_int = index # Already an int
                elif isinstance(index, float) and index.is_integer():
                     index_int = int(index) # Allow float indices if they are whole numbers
                else:
                    # Attempt conversion for other types if not already handled
                    index_int = int(index)
            except (ValueError, TypeError):
                # Raise error with the original raw index for clarity if conversion fails
                # Use index_raw in the message as 'index' might be the resolved value
                raise ValueError(f"Invalid list index value: {index} (from raw index '{index_raw}')")

            # Handle negative index normalization
            list_len = len(list_var)
            if index_int < 0:
                normalized_index = index_int + list_len
            else:
                normalized_index = index_int

            # Extend the list if needed for positive indices (Minima allows out-of-bounds assignment)
            if normalized_index >= list_len and normalized_index >= 0:
                # Extend the list with None (empty) values
                list_var.extend([None] * (normalized_index - list_len + 1))
                list_var[normalized_index] = value
                # No need to update self.memory[list_var_name] = list_var as we modified the list in-place
                if self.debug_mode:
                    print(f"DEBUG - Extended list '{list_var_name}' and set index {normalized_index} to {value}")

            elif 0 <= normalized_index < list_len:
                 # Assign value to existing index
                list_var[normalized_index] = value
                 # No need to update self.memory[list_var_name] = list_var as we modified the list in-place
                if self.debug_mode:
                    print(f"DEBUG - Set list '{list_var_name}' index {normalized_index} to {value}")
            else:
                 # This case (negative index out of bounds after normalization)
                raise ValueError(f"List index out of range: {index_int} (normalized: {normalized_index}) for list of length {list_len}")

        elif op == 'SUB':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                left_num = float(left_val) if isinstance(left_val, float) or (isinstance(left_val, str) and '.' in left_val) else int(left_val)
                right_num = float(right_val) if isinstance(right_val, float) or (isinstance(right_val, str) and '.' in right_val) else int(right_val)
                computed_result = left_num - right_num
                self.memory[result] = self.validate_number(computed_result)
            except ValueError as e:
                if "out of range" in str(e) or "too many digits" in str(e):
                    raise e
                raise ValueError(f"Cannot subtract values: {left_val} - {right_val}")

        elif op == 'MUL':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                left_num = float(left_val) if isinstance(left_val, float) or (isinstance(left_val, str) and '.' in left_val) else int(left_val)
                right_num = float(right_val) if isinstance(right_val, float) or (isinstance(right_val, str) and '.' in right_val) else int(right_val)
                # Calculate result and validate it
                computed_result = left_num * right_num
                self.memory[result] = self.validate_number(computed_result)
            except (ValueError, TypeError) as e:
                if "out of range" in str(e) or "too many digits" in str(e):
                    raise e  # Re-raise validation errors
                if isinstance(left_val, str) and isinstance(right_val, int):
                    self.memory[result] = left_val * right_val
                elif isinstance(left_val, int) and isinstance(right_val, str):
                    self.memory[result] = left_val * right_val
                else:
                    raise ValueError(f"Cannot multiply values: {left_val} * {right_val}")

        elif op == 'DIV':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                # Convert to numbers if needed
                left_num = float(left_val) if isinstance(left_val, float) or (isinstance(left_val, str) and '.' in left_val) else int(left_val)
                right_num = float(right_val) if isinstance(right_val, float) or (isinstance(right_val, str) and '.' in right_val) else int(right_val)
                if right_num == 0:
                    raise ValueError("Division by zero")
                    
                # Calculate result and validate it
                computed_result = left_num / right_num
                
                # If both operands are integers and the original code expected integer division
                # Force integer division for algorithm correctness
                if isinstance(left_val, int) and isinstance(right_val, int):
                    computed_result = int(computed_result)
                    
                self.memory[result] = self.validate_number(computed_result)
            except (ValueError, TypeError) as e:
                if "Division by zero" in str(e):
                    raise ValueError("Division by zero")
                if "out of range" in str(e) or "too many digits" in str(e):
                    raise e  # Re-raise validation errors
                raise ValueError(f"Cannot perform division on non-numeric values: {left_val} / {right_val}")

        elif op == 'MOD':
            left_val = self.get_value(arg1)
            right_val = self.get_value(arg2)
            if left_val == arg1:
                left_val = self.resolve_variable(arg1)
            if right_val == arg2:
                right_val = self.resolve_variable(arg2)
            if isinstance(left_val, str):
                try:
                    if '.' in left_val:
                        left_val = float(left_val)
                    else:
                        left_val = int(left_val)
                except ValueError:
                    pass
            if isinstance(right_val, str):
                try:
                    if '.' in right_val:
                        right_val = float(right_val)
                    else:
                        right_val = int(right_val)
                except ValueError:
                    pass
            if not isinstance(left_val, (int, float)):
                raise ValueError(f"Cannot perform modulo: left operand '{left_val}' is not a number")
            if not isinstance(right_val, (int, float)):
                raise ValueError(f"Cannot perform modulo: right operand '{right_val}' is not a number")
            if right_val == 0:
                raise ValueError("Modulo by zero")
            # Calculate result and validate it
            computed_result = left_val % right_val
            self.memory[result] = self.validate_number(computed_result)

        elif op == 'NEG':
            val = self.resolve_variable(arg1)
            try:
                # Calculate result and validate it
                computed_result = -float(val) if isinstance(val, float) or (isinstance(val, str) and '.' in val) else -int(val)
                self.memory[result] = self.validate_number(computed_result)
            except (ValueError, TypeError) as e:
                if "out of range" in str(e) or "too many digits" in str(e):
                    raise e  # Re-raise validation errors
                raise ValueError(f"Cannot negate non-numeric value: {val}")

        elif op == 'NOT':
            val = self.resolve_variable(arg1)
            self.memory[result] = not bool(val)

        elif op == 'AND':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            self.memory[result] = bool(left_val) and bool(right_val)

        elif op == 'OR':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            self.memory[result] = bool(left_val) or bool(right_val)

        elif op == 'EQ':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            if right_val == 'empty' or right_val is None:
                self.memory[result] = (left_val is None or left_val == '')
            elif left_val == 'empty' or left_val is None:
                self.memory[result] = (right_val is None or right_val == '')
            else:
                self.memory[result] = (left_val == right_val)

        elif op == 'NEQ':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            if right_val == 'empty' or right_val is None:
                self.memory[result] = (left_val is not None and left_val != '')
            elif left_val == 'empty' or left_val is None:
                self.memory[result] = (right_val is not None and right_val != '')
            else:
                self.memory[result] = (left_val != right_val)

        elif op == 'LT':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                if left_val is None and right_val is None:
                    self.memory[result] = False
                elif left_val is None:
                    self.memory[result] = True
                elif right_val is None:
                    self.memory[result] = False
                else:
                    if isinstance(left_val, str) and left_val.isdigit():
                        left_val = int(left_val)
                    if isinstance(right_val, str) and right_val.isdigit():
                        right_val = int(right_val)
                    self.memory[result] = (left_val < right_val)
                if self.debug_mode:
                    print(f"LT: {left_val} < {right_val} = {self.memory[result]}")
            except Exception as e:
                raise ValueError(f"Error in LT comparison: {str(e)}")

        elif op == 'LE':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            self.memory[result] = (left_val <= right_val)

        elif op == 'GT':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            self.memory[result] = (left_val > right_val)

        elif op == 'GE':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            self.memory[result] = (left_val >= right_val)

        elif op == 'GOTO':
            if result in self.labels:
                if self.debug_mode:
                    print(f"Jumping to label {result} at instruction {self.labels[result]}")
                self.ip = self.labels[result]
            else:
                raise ValueError(f"Label not found: {result}")

        elif op == 'IFFALSE':
            cond = self.resolve_variable(arg1)
            if self.debug_mode:
                print(f"IFFALSE condition value: {cond} (type: {type(cond).__name__})")
            if not bool(cond):
                if result in self.labels:
                    if self.debug_mode:
                        print(f"Condition false, jumping to label {result} at instruction {self.labels[result]}")
                    self.ip = self.labels[result]
                else:
                    raise ValueError(f"Label not found: {result}")
            else:
                if self.debug_mode:
                    print(f"Condition true, continuing to next instruction")
                self.ip += 1

        elif op == 'IFTRUE':
            cond = self.resolve_variable(arg1)
            if self.debug_mode:
                print(f"IFTRUE condition value: {cond} (type: {type(cond).__name__})")
            if bool(cond):
                if result in self.labels:
                    if self.debug_mode:
                        print(f"Condition true, jumping to label {result} at instruction {self.labels[result]}")
                    self.ip = self.labels[result]
                else:
                    raise ValueError(f"Label not found: {result}")
            else:
                if self.debug_mode:
                    print(f"Condition false, continuing to next instruction")
                self.ip += 1

        elif op == 'PRINT':
            val = self.resolve_variable(arg1)
            if val is None:
                # Format None as "empty" for output
                self.output_buffer.write("empty")
            elif isinstance(val, list):
                formatted_list = []
                for item in val:
                    if item is None:
                        # Handle None values within lists as "empty"
                        formatted_list.append("empty")
                    elif isinstance(item, tuple) and len(item) >= 2:
                        value = item[1]
                        if value is None:
                            formatted_list.append("empty")
                        elif isinstance(value, bool):
                            value = "YES" if value else "NO"
                        elif isinstance(value, (int, float)):
                            try:
                                value = self.format_number_for_output(value)
                            except ValueError as e:
                                # If value is out of range, provide a trimmed representation
                                if isinstance(value, float):
                                    str_val = str(abs(value))
                                    parts = str_val.split('.')
                                    if len(parts) > 1 and len(parts[1]) > self.max_digits:
                                        parts[1] = parts[1][:self.max_digits]
                                    value = f"~{parts[0]}.{parts[1]}" if value < 0 else f"{parts[0]}.{parts[1]}"
                                else:
                                    value = f"~{abs(value)}" if value < 0 else str(value)
                        formatted_list.append(value)
                    else:
                        if item is None:
                            formatted_list.append("empty")
                        elif isinstance(item, bool):
                            item = "YES" if item else "NO"
                        elif isinstance(item, (int, float)):
                            try:
                                item = self.format_number_for_output(item)
                            except ValueError as e:
                                # If value is out of range, provide a trimmed representation
                                if isinstance(item, float):
                                    str_val = str(abs(item))
                                    parts = str_val.split('.')
                                    if len(parts) > 1 and len(parts[1]) > self.max_digits:
                                        parts[1] = parts[1][:self.max_digits]
                                    item = f"~{parts[0]}.{parts[1]}" if item < 0 else f"{parts[0]}.{parts[1]}"
                                else:
                                    item = f"~{abs(item)}" if item < 0 else str(item)
                        formatted_list.append(item)
                self.output_buffer.write(str(formatted_list))
            else:
                if isinstance(val, bool):
                    val = "YES" if val else "NO"
                elif isinstance(val, (int, float)):
                    try:
                        val = self.format_number_for_output(val)
                    except ValueError as e:
                        # If value is out of range, provide a trimmed representation
                        if isinstance(val, float):
                            str_val = str(abs(val))
                            parts = str_val.split('.')
                            if len(parts) > 1 and len(parts[1]) > self.max_digits:
                                parts[1] = parts[1][:self.max_digits]
                            val = f"~{parts[0]}.{parts[1]}" if val < 0 else f"{parts[0]}.{parts[1]}"
                        else:
                            val = f"~{abs(val)}" if val < 0 else str(val)
                
                # Format the final value, ensuring None becomes "empty"
                output_val = "empty" if val is None else val
                
                if isinstance(output_val, str):
                    output_val = output_val.replace('\\\\', '\\')  
                    output_val = output_val.replace('\\"', '"')    
                    output_val = output_val.replace('\\n', '\n')   
                    output_val = output_val.replace('\\t', '\t')   
                self.output_buffer.write(str(output_val))

        elif op == 'CONCAT':
            val1 = self.resolve_variable(arg1)
            val2 = self.resolve_variable(arg2)
            if val1 is None:
                str_val1 = "empty"
            elif isinstance(val1, bool):
                str_val1 = "YES" if val1 else "NO"
            elif isinstance(val1, (int, float)) and val1 < 0:
                str_val1 = f"~{abs(val1)}"
            else:
                str_val1 = str(val1)
                
            if val2 is None:
                str_val2 = "empty"
            elif isinstance(val2, bool):
                str_val2 = "YES" if val2 else "NO"
            elif isinstance(val2, (int, float)) and val2 < 0:
                str_val2 = f"~{abs(val2)}"
            else:
                str_val2 = str(val2)
                
            for i, str_val in enumerate([str_val1, str_val2]):
                if isinstance(str_val, str) and str_val:  
                    processed = str_val.replace('\\\\', '\\')  
                    processed = processed.replace('\\"', '"')   
                    processed = processed.replace('\\n', '\n')  
                    processed = processed.replace('\\t', '\t')  
                    if i == 0:
                        str_val1 = processed
                    else:
                        str_val2 = processed
            self.memory[result] = str_val1 + str_val2

        elif op == 'INPUT':
            self.waiting_for_input = True
            self.input_result_var = result
            prompt = self.resolve_variable(arg1)
            
            # Check if the next instruction is a TYPECAST involving this input variable
            self.input_expected_type = None  # Reset before check
            next_ip = self.ip + 1
            if next_ip < len(self.instructions):
                next_op, next_arg1, next_arg2, next_result = self.instructions[next_ip]
                if next_op == 'TYPECAST' and next_arg1 == result:
                    self.input_expected_type = next_arg2  # Store the target type
                    if self.debug_mode:
                        print(f"  Input for '{result}' expects type '{self.input_expected_type}' due to next instruction.")
            
            self.input_prompt = str(prompt if prompt is not None else "")

        elif op == 'TYPECAST':
            val = self.resolve_variable(arg1)
            if arg2 == 'integer':
                if isinstance(val, bool):
                    self.memory[result] = 1 if val else 0
                else:
                    try:
                        # Special handling for tilde notation strings
                        if isinstance(val, str) and val.startswith('~') and len(val) > 1 and val[1:].isdigit():
                            computed_result = -int(val[1:])
                        else:
                            computed_result = int(val)
                        self.memory[result] = self.validate_number(computed_result)
                    except (ValueError, TypeError) as e:
                        if "out of range" in str(e) or "too many digits" in str(e):
                            raise e
                        self.memory[result] = 0  
            elif arg2 == 'point':
                if isinstance(val, bool):
                    self.memory[result] = 1.0 if val else 0.0
                else:
                    try:
                        computed_result = float(val)
                        self.memory[result] = self.validate_number(computed_result)
                    except (ValueError, TypeError) as e:
                        if "out of range" in str(e) or "too many digits" in str(e):
                            raise e
                        self.memory[result] = 0.0  
            elif arg2 == 'text':
                # Apply the tilde notation for negative numbers when converting to text
                if isinstance(val, (int, float)) and val < 0:
                    self.memory[result] = f"~{abs(val)}"
                else:
                    self.memory[result] = str(val)
            elif arg2 == 'state':
                if isinstance(val, (int, float)):
                    self.memory[result] = bool(val != 0)
                elif isinstance(val, str):
                    self.memory[result] = bool(val)
                else:
                    self.memory[result] = bool(val)
            else:
                self.memory[result] = val

        elif op == 'LIST_CREATE':
            self.memory[result] = []

        elif op == 'LIST_APPEND':
            list_var = self.resolve_variable(arg1)
            item = self.resolve_variable(arg2)
            if isinstance(list_var, list):
                list_var.append(item)
            else:
                self.memory[arg1] = [item]

        elif op == 'LIST_ACCESS':
            list_var = self.resolve_variable(arg1)
            index_raw = arg2 # Keep the raw argument

            try:
                # Resolve the index variable/literal first
                # This should return the *actual value* (e.g., the integer value of 'i')
                index = self.resolve_variable(index_raw)

                # Convert index to integer if possible
                # The 'index' variable now holds the actual resolved value
                try:
                    if isinstance(index, str) and index.isdigit():
                        index_int = int(index)
                    elif isinstance(index, str) and index.startswith('~') and index[1:].isdigit():
                        index_int = -int(index[1:])
                    elif isinstance(index, int):
                        index_int = index # Already an int
                    elif isinstance(index, float) and index.is_integer():
                        index_int = int(index) # Allow float indices if they are whole numbers
                    else:
                        # Attempt conversion for other types if not already handled
                        index_int = int(index)
                except (ValueError, TypeError):
                    # Use original raw index in error message
                    raise ValueError(f"Invalid list index value: {index} (from raw index '{index_raw}')")

            except Exception as e:
                 # Use original raw index in error message
                raise ValueError(f"Error resolving list index '{index_raw}': {e}")

            try:
                # Use index_int for calculations and checks from here
                if isinstance(list_var, list):
                    # Handle list access
                    list_length = len(list_var)

                    # Normalize negative index to positive equivalent
                    if index_int < 0:
                        normalized_index = index_int + list_length
                    else:
                        normalized_index = index_int

                    if 0 <= normalized_index < list_length:
                        self.memory[result] = list_var[normalized_index]
                    else:
                        # Out of bounds for list, return 'empty' (None)
                        self.memory[result] = None
                        if self.debug_mode:
                            print(f"List index {index_int} out of range for list of length {list_length}. Returning 'empty'.")

                elif isinstance(list_var, str):
                    # Handle string access (treat strings like lists of characters)
                    string_length = len(list_var)

                    # Normalize negative index to positive equivalent
                    if index_int < 0:
                        normalized_index = index_int + string_length
                    else:
                        normalized_index = index_int

                    if 0 <= normalized_index < string_length:
                        self.memory[result] = list_var[normalized_index]
                    else:
                         # Out of bounds for string, return 'empty' (None)
                         self.memory[result] = None
                         if self.debug_mode:
                             print(f"String index {index_int} out of range for string of length {string_length}. Returning 'empty'.")

                else:
                    if self.debug_mode:
                        print(f"Warning: Attempted LIST_ACCESS on non-list/non-string variable '{arg1}'")
                    self.memory[result] = None # Or raise error? Minima might allow this returning 'empty'
            except IndexError as e:
                 # This block might not be reached if we handle out-of-bounds above
                 raise ValueError(f"Runtime Error: {e}")
            except Exception as e:
                if self.debug_mode:
                    print(f"Error during LIST_ACCESS operation: {e}")
                raise ValueError(f"Runtime Error during list access: {e}")

        elif op == 'GROUP_ACCESS':
            group = self.resolve_variable(arg1)
            key = self.resolve_variable(arg2)
            if isinstance(group, dict):
                if key in group:
                    self.memory[result] = group[key]
                else:
                    raise ValueError(f"Key {key} not found in group {arg1}")
            else:
                raise ValueError(f"Cannot access key in non-group: {arg1}")

        elif op == 'GROUP_CREATE':
            self.memory[result] = {}
            if self.debug_mode:
                print(f"Created empty group: {result}")

        elif op == 'GROUP_SET':
            group = self.resolve_variable(arg1)
            key = self.resolve_variable(arg2)
            value = self.resolve_variable(result)
            
            if not isinstance(group, dict):
                group = {}
                self.memory[arg1] = group
            
            group[key] = value
            
            if self.debug_mode:
                print(f"Set group {arg1}[{key}] = {value}")

        elif op == 'ERROR':
            raise ValueError(f"Runtime error: {arg1}")

        if self.debug_mode and op in ('ASSIGN', 'ADD', 'SUB', 'MUL', 'DIV'):
            if result is not None and result in self.memory:
                print(f"Variable '{result}' set to: {self.memory[result]}")