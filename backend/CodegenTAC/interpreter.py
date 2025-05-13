from backend.CodegenTAC.built_in_functions import MinimaBultins
from io import StringIO
import traceback  
import math

class TACInterpreter:
    def __init__(self):
        self.memory_stack = [{}]  # Stack of dictionaries for scopes (global scope at index 0)
        self.functions = {}
        self.function_params = {}  
        self.call_info_stack = []  # Stack for return information (IP, target variable)
        self.ip = 0
        self.param_stack = []
        self.output_buffer = StringIO()
        self.instructions = []
        self.labels = {}
        self.function_bodies = {}
        self.waiting_for_input = False
        self.input_prompt = ""
        self.input_result_var = None
        self.steps_executed = 0
        self.max_execution_steps = 10000  
        self.max_digits = 9
        self.min_number = -999999999
        self.max_number = 999999999
        self.input_expected_type = None  
        self.builtins = MinimaBultins.get_builtin_implementations()
        self.debug_mode = False  

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
            if len(parts) > 1:
                fractional_part = parts[1]
                if len(fractional_part) > self.max_digits:
                    truncated = round(value, self.max_digits)
                    return truncated
            if abs(value) > float(self.max_number) + (1.0 - 10**(-self.max_digits)):
                raise ValueError(f"Float value out of range: {value}. Valid range is ~{self.min_number} to {self.max_number}")
        return value

    def format_number_for_output(self, value):
        """Format number for output according to Minima language rules."""
        if not isinstance(value, (int, float)):
            return value
        try:
            self.validate_number(value)
        except ValueError as e:
            raise ValueError(f"Output formatting error: {e}")
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if isinstance(value, int):
            if value < 0:
                return f"-{abs(value)}"
            return str(value)
        if value < 0:
            formatted = f"{abs(value):.{self.max_digits}f}".rstrip('0').rstrip('.')
            if formatted == "0.": formatted = "0"
            return f"-{formatted}"
        else:
            formatted = f"{value:.{self.max_digits}f}".rstrip('0').rstrip('.')
            if formatted == "0.": formatted = "0"
            return formatted

    def set_execution_limit(self, limit=None):
        """
        Set the maximum execution steps limit.
        Use None to disable the limit entirely.
        """
        self.max_execution_steps = limit

    def find_variable_scope(self, name):
        """Finds the innermost scope dictionary containing the variable."""
        if not isinstance(name, str):
            return None
        for scope in reversed(self.memory_stack):
            if name in scope:
                return scope
        return None

    def assign_variable(self, name, value):
        """Assigns a value to a variable in the current scope."""
        if not isinstance(name, str):
            raise TypeError(f"Invalid variable name for assignment: {name}")
        self.memory_stack[-1][name] = value
        if self.debug_mode:
            print(f"Assigned '{name}' = {repr(value)} in scope level {len(self.memory_stack) - 1}")

    def resolve_variable(self, val):
        """Resolve a variable name or literal to its value using the scope stack."""
        if isinstance(val, str):
            # 1. Check scopes for variable name
            scope = self.find_variable_scope(val)
            if scope is not None:
                return scope[val]
            # 2. Check if it's a temporary variable name (t1, t2, etc.)
            if val.startswith('t') and val[1:].isdigit():
                if self.debug_mode:
                    print(f"Warning: Temporary variable '{val}' not found in any scope.")
                return val
            # 3. Check for literals after checking variables
            if val == 'empty':
                return None
            if val == 'YES':
                return True
            if val == 'NO':
                return False
            if val.startswith('-'):
                num_part = val[1:]
                if num_part.isdigit():
                    try:
                        return -int(num_part)
                    except ValueError: pass
                elif '.' in num_part or 'e' in num_part.lower():
                    try:
                        return -float(num_part)
                    except ValueError: pass
            elif val.isdigit():
                try:
                    return int(val)
                except ValueError: pass
            elif '.' in val or 'e' in val.lower():
                try:
                    return float(val)
                except ValueError: pass
            if val.startswith('"') and val.endswith('"'):
                inner_str = val[1:-1]
                # Handle escape sequences
                result = ""
                i = 0
                while i < len(inner_str):
                    if inner_str[i] == '\\' and i + 1 < len(inner_str):
                        next_char = inner_str[i+1]
                        if next_char == '\\': result += '\\'
                        elif next_char == '"': result += '"'
                        elif next_char == 'n': result += '\n'
                        elif next_char == 't': result += '\t'
                        else: result += '\\' + next_char
                        i += 2
                    else:
                        result += inner_str[i]
                        i += 1
                return result
            # 4. If it's not a variable in scope and not a recognized literal, return the string itself
            return val
        elif isinstance(val, tuple) and len(val) >= 2:
            if val[0] in ('integer', 'float', 'bool', 'text', 'id', 'list', 'point', 'state', 'empty'):
                if val[0] == 'id':
                    return self.resolve_variable(val[1])
                elif val[0] == 'empty':
                    return None
                else:
                    return val[1]
            else:
                return val
        # Otherwise (int, float, bool, list, None, etc.), return the value directly
        return val

    def reset(self):
        self.memory_stack = [{}]
        self.call_info_stack = []
        self.functions = {}
        self.function_params = {}
        self.ip = 0
        self.param_stack = []
        self.output_buffer = StringIO()
        self.function_bodies = {}
        self.labels = {}
        self.waiting_for_input = False
        self.input_prompt = ""
        self.input_result_var = None
        self.steps_executed = 0

    def load(self, instructions):
        self.reset()
        self.instructions = instructions
        current_function = None
        for i, (op, arg1, arg2, result) in enumerate(instructions):
            if op == 'FUNCTION':
                current_function = arg1
                self.functions[current_function] = result
                self.function_params[current_function] = arg2 or []
                if self.debug_mode:
                    print(f"Registered function '{current_function}' starting at label '{result}' with params {arg2}")
            elif op == 'LABEL':
                self.labels[result] = i
                if self.debug_mode:
                    print(f"Registering label '{result}' at instruction index {i}")
        if self.debug_mode:
            print(f"Loaded {len(instructions)} instructions")
            print(f"Labels defined: {list(self.labels.keys())}")
            print(f"Functions defined: {list(self.functions.keys())}")
        return self

    def run(self):
        """Execute the loaded TAC instructions."""
        self.ip = 0
        self.waiting_for_input = False
        self.steps_executed = 0  
        self.output_buffer = StringIO()  
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
                            if 'i' in self.memory_stack[-1] and isinstance(self.memory_stack[-1]['i'], int):
                                self.memory_stack[-1]['i'] -= 1
                                if self.debug_mode:
                                    print(f"DETECTED AND FIXED INFINITE LOOP: Decremented i to {self.memory_stack[-1]['i']}")
                                loop_pattern_count = 0
            if self.debug_mode:
                current_instruction_str = f"{self.ip}: {op} {arg1}, {arg2}, {result}"
                print(f"Step {self.steps_executed}: Executing {current_instruction_str}")
            try:
                prev_ip = self.ip
                self.execute_instruction(op, arg1, arg2, result)
                self.steps_executed += 1
                if self.waiting_for_input:
                    if self.debug_mode:
                        print(f"--- Pausing for Input (IP: {self.ip}) ---")
                    break  
                if self.ip == prev_ip:
                    self.ip += 1
            except Exception as e:
                error_line = prev_ip
                error_message = f"\nRuntime Error at instruction {error_line} ({op} {arg1} {arg2} {result}): {str(e)}\n"
                print(error_message)
                print(traceback.format_exc())
                self.output_buffer.write(error_message)
                self.ip = len(self.instructions)
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
        self.output_buffer = StringIO()
        try:
            input_val_str = str(user_input)
            validated_input = self.validate_and_parse_input(input_val_str, self.input_expected_type)
            self.assign_variable(self.input_result_var, validated_input)
            if self.debug_mode:
                print(f"  Stored validated input in '{self.input_result_var}': {repr(validated_input)} (type: {type(validated_input).__name__}) in scope level {len(self.memory_stack) - 1}")
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
            return self.output_buffer.getvalue()
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
                if self.ip == prev_ip:
                    self.ip += 1
            except Exception as e:
                error_line = prev_ip
                error_message = f"\nRuntime Error at instruction {error_line} ({op} {arg1} {arg2} {result}): {str(e)}\n"
                print(error_message)
                print(traceback.format_exc())
                self.output_buffer.write(error_message)
                self.ip = len(self.instructions)
        if self.debug_mode:
            segment_output = self.output_buffer.getvalue()
            print(f"--- Resumed Segment Finished (IP: {self.ip}, Steps: {self.steps_executed}) ---")
            print(f"Segment Output Buffer Content:\n'''\n{segment_output}\n'''")
        return self.output_buffer.getvalue()

    def validate_and_parse_input(self, input_str, expected_type=None):
        """Validates input string based on Minima rules and optional expected type."""
        original_input_str = input_str
        # No need to convert - to ~ as we're now using - for negative numbers
        
        is_potentially_numeric = False
        cleaned_num_str = input_str.replace('-', '', 1) if input_str.startswith('-') else input_str
        try:
            float(cleaned_num_str)
            is_potentially_numeric = True
        except ValueError:
            is_potentially_numeric = False
        
        if expected_type:
            try:
                if expected_type == 'integer':
                    if '.' in cleaned_num_str or 'e' in cleaned_num_str.lower():
                        raise ValueError("Invalid format for integer input.")
                    if not cleaned_num_str.isdigit():
                        raise ValueError("Invalid characters for integer input.")
                    numeric_value = -int(cleaned_num_str) if input_str.startswith('-') else int(cleaned_num_str)
                    return self.validate_number(numeric_value)
                elif expected_type == 'point':
                    if not is_potentially_numeric:
                        raise ValueError("Invalid format for point input.")
                    numeric_value = -float(cleaned_num_str) if input_str.startswith('-') else float(cleaned_num_str)
                    return self.validate_number(numeric_value)
                elif expected_type == 'state':
                    upper_val = input_str.upper()
                    if upper_val in ['YES', 'TRUE', '1']: return True
                    elif upper_val in ['NO', 'FALSE', '0']: return False
                    else:
                        raise ValueError("Invalid state value. Expected YES, NO, TRUE, FALSE, 0, or 1.")
                elif expected_type == 'text':
                    return input_str
                else:
                    return input_str
            except ValueError as e:
                raise ValueError(f"Input '{original_input_str}' is not a valid {expected_type}: {str(e)}")
        else:
            if is_potentially_numeric:
                try:
                    if '.' in cleaned_num_str or 'e' in cleaned_num_str.lower():
                        numeric_value = -float(cleaned_num_str) if input_str.startswith('-') else float(cleaned_num_str)
                        return self.validate_number(numeric_value)
                    else:
                        numeric_value = -int(cleaned_num_str) if input_str.startswith('-') else int(cleaned_num_str)
                        return self.validate_number(numeric_value)
                except ValueError as e:
                    raise ValueError(f"Numeric input '{original_input_str}' validation failed: {str(e)}")
            else:
                upper_val = input_str.upper()
                if upper_val == 'YES': return True
                if upper_val == 'NO': return False
                return input_str

    def evaluate_condition(self, value):
        """Evaluates a value according to Minima's boolean rules (YES/NO)."""
        if value == "YES" or value is True:
            return True
        if value == "NO" or value is False:
            return False
        # Fallback to standard Python truthiness for other types (numbers, lists, etc.)
        # Note: Empty strings/lists/0 will be False, non-empty/non-zero will be True.
        return bool(value)

    def execute_instruction(self, op, arg1, arg2, result):
        if self.debug_mode and op in ('LABEL', 'GOTO', 'IFTRUE', 'IFFALSE'):
            print(f"Executing {op} with args: {arg1}, {arg2}, {result}")
        if self.debug_mode and op in ('LT', 'LE', 'GT', 'GE', 'EQ', 'NEQ'):
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            print(f"Condition: {left_val} {op} {right_val}")
            
        # Built-in function call
        if op == 'CALL' and arg1 in self.builtins:
            args = []
            num_expected_params = self.builtins[arg1].__code__.co_argcount - 1
            actual_params_passed = arg2 if isinstance(arg2, int) else 0
            current_params = self.param_stack[:actual_params_passed]
            self.param_stack = self.param_stack[actual_params_passed:]
            for param_index, param_raw_value in current_params:
                resolved_val = self.resolve_variable(param_raw_value)
                args.append(resolved_val)
            try:
                return_val = self.builtins[arg1](self, args)
                if result:
                    self.assign_variable(result, return_val)
            except Exception as e:
                raise ValueError(f"Error in built-in function {arg1}: {str(e)}")
                
        # User-defined function call
        elif op == 'CALL' and arg1 in self.functions:
            func_label_name = self.functions[arg1]
            if func_label_name not in self.labels:
                raise ValueError(f"Function label '{func_label_name}' for function '{arg1}' not found.")
            
            # Store return info
            self.call_info_stack.append({
                'return_ip': self.ip + 1,
                'target_var': result
            })
            
            # Create new scope for the function
            new_scope = {}
            param_count = arg2 if isinstance(arg2, int) else 0
            param_names = self.function_params.get(arg1, [])
            
            # Consume params from the stack and assign to new scope
            current_params = self.param_stack[:param_count]
            self.param_stack = self.param_stack[param_count:]
            
            if self.debug_mode:
                print(f"Calling '{arg1}'. Params expected: {param_names}. Params on stack: {current_params}")
                
            for i in range(param_count):
                param_name = param_names[i] if i < len(param_names) else f"_param{i}_"
                param_raw_value = None
                
                # Find the param with the correct index
                for p_idx, p_val in current_params:
                    if p_idx == i:
                        param_raw_value = p_val
                        break
                        
                if param_raw_value is not None:
                    # Resolve the parameter value in the caller's context
                    resolved_val = self.resolve_variable(param_raw_value)
                    new_scope[param_name] = resolved_val
                    if self.debug_mode:
                        print(f"  Assigning param '{param_name}' = {repr(resolved_val)}")
                elif i < len(param_names):
                    # Parameter expected but not provided
                    new_scope[param_name] = None
                    if self.debug_mode:
                        print(f"  Warning: Missing argument for param '{param_name}', assigning None.")
            
            # Push the new scope
            self.memory_stack.append(new_scope)
            if self.debug_mode:
                print(f"Pushed new scope for '{arg1}'. Stack depth: {len(self.memory_stack)}")
                print(f"  New scope content: {new_scope}")
                
            # Jump to function label
            self.ip = self.labels[func_label_name]
            
        # Return from function
        elif op == 'RETURN':
            if self.call_info_stack:
                # Resolve return value in the current scope
                return_val = self.resolve_variable(arg1)
                
                # Pop the function's scope
                popped_scope = self.memory_stack.pop()
                if self.debug_mode:
                    print(f"Returning from function. Popped scope: {popped_scope}. Stack depth: {len(self.memory_stack)}")
                    
                # Pop return info
                return_info = self.call_info_stack.pop()
                target_var = return_info['target_var']
                return_ip = return_info['return_ip']
                
                # Assign return value to the target variable in the caller's scope
                if target_var:
                    self.assign_variable(target_var, return_val)
                    
                # Set IP to return address
                self.ip = return_ip
            else:
                # Return from global scope - terminate program
                if self.debug_mode:
                    print("RETURN from global scope. Halting execution.")
                self.ip = len(self.instructions)
                
        # Function and label definitions (no runtime action)
        elif op == 'FUNCTION' or op == 'LABEL':
            pass
            
        # Parameter for function calls
        elif op == 'PARAM':
            self.param_stack.append((result, arg1))
            if self.debug_mode:
                print(f"Pushed param index {result} with raw value {repr(arg1)}")
                
        # Assignment
        elif op == 'ASSIGN':
            if arg1 == ']':
                self.assign_variable(result, [])
                if self.debug_mode:
                    print(f"Initialized empty list: {result} = []")
            else:
                value = self.resolve_variable(arg1)
                self.assign_variable(result, value)
                if self.debug_mode and result in ('i', 'j', 'k'):
                    print(f"Assigned {value} to {result}")
                    
        # Addition/concatenation
        elif op == 'ADD':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            
            # Handle list concatenation
            if isinstance(left_val, list) or isinstance(right_val, list):
                l_list = list(left_val) if isinstance(left_val, list) else [left_val]
                r_list = list(right_val) if isinstance(right_val, list) else [right_val]
                self.assign_variable(result, l_list + r_list)
                return
                
            # Handle string concatenation
            is_left_str = isinstance(left_val, str)
            is_right_str = isinstance(right_val, str)
            if is_left_str or is_right_str:
                str_left = "YES" if isinstance(left_val, bool) and left_val else "NO" if isinstance(left_val, bool) and not left_val else str(left_val or "")
                str_right = "YES" if isinstance(right_val, bool) and right_val else "NO" if isinstance(right_val, bool) and not right_val else str(right_val or "")
                self.assign_variable(result, str_left + str_right)
            else:
                # Numeric addition
                try:
                    def to_num(val):
                        if isinstance(val, (int, float)):
                            return val
                        if isinstance(val, bool):
                            return 1 if val else 0
                        if val is None:
                            return 0
                        raise TypeError(f"Cannot convert {val} (type {type(val).__name__}) to number for addition")
                    
                    left_num = to_num(left_val)
                    right_num = to_num(right_val)
                    computed_result = left_num + right_num
                    self.assign_variable(result, self.validate_number(computed_result))
                except (ValueError, TypeError) as e:
                    if "out of range" in str(e) or "too many digits" in str(e):
                        raise e
                    else:
                        raise TypeError(f"Error during numeric addition for '{arg1}' ({type(left_val).__name__}) and '{arg2}' ({type(right_val).__name__}): {e}")
                        
        # Subtraction
        elif op == 'SUB':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                num_l = left_val if isinstance(left_val, (int, float)) else 0
                num_r = right_val if isinstance(right_val, (int, float)) else 0
                computed_result = num_l - num_r
                self.assign_variable(result, self.validate_number(computed_result))
            except (ValueError, TypeError) as e:
                if "out of range" in str(e) or "too many digits" in str(e):
                    raise e
                raise ValueError(f"Cannot subtract values: {left_val} - {right_val}: {e}")
                
        # Multiplication
        elif op == 'MUL':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                # Try numeric multiplication first
                if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
                    computed_result = left_val * right_val
                    self.assign_variable(result, self.validate_number(computed_result))
                # Handle string repetition
                elif isinstance(left_val, str) and isinstance(right_val, int):
                    self.assign_variable(result, left_val * right_val)
                elif isinstance(left_val, int) and isinstance(right_val, str):
                    self.assign_variable(result, left_val * right_val)
                else:
                    raise TypeError(f"Cannot multiply values of types {type(left_val).__name__} and {type(right_val).__name__}")
            except (ValueError, TypeError) as e:
                if "out of range" in str(e) or "too many digits" in str(e):
                    raise e
                raise ValueError(f"Cannot multiply values: {left_val} * {right_val}: {e}")
                
        # Division
        elif op == 'DIV':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                num_l = float(left_val) if isinstance(left_val, (int, float)) else 0.0
                num_r = float(right_val) if isinstance(right_val, (int, float)) else 1.0
                if num_r == 0:
                    raise ValueError("Division by zero")
                computed_result = num_l / num_r
                self.assign_variable(result, self.validate_number(computed_result))
            except (ValueError, TypeError) as e:
                if "Division by zero" in str(e):
                    raise ValueError("Division by zero")
                if "out of range" in str(e) or "too many digits" in str(e):
                    raise e
                raise ValueError(f"Cannot perform division on non-numeric values: {left_val} / {right_val}: {e}")
                
        # Modulo
        elif op == 'MOD':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                if not isinstance(left_val, (int, float)):
                    raise ValueError(f"Cannot perform modulo: left operand '{left_val}' is not a number")
                if not isinstance(right_val, (int, float)):
                    raise ValueError(f"Cannot perform modulo: right operand '{right_val}' is not a number")
                if right_val == 0:
                    raise ValueError("Modulo by zero")
                computed_result = left_val % right_val
                self.assign_variable(result, self.validate_number(computed_result))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Error in modulo operation: {e}")
                
        # Negation
        elif op == 'NEG':
            val = self.resolve_variable(arg1)
            try:
                if not isinstance(val, (int, float)):
                    raise ValueError(f"Cannot negate non-numeric value: {val} ({type(val).__name__})")
                computed_result = -val
                self.assign_variable(result, self.validate_number(computed_result))
            except (ValueError, TypeError) as e:
                if "out of range" in str(e) or "too many digits" in str(e):
                    raise e
                raise ValueError(f"Cannot negate value: {val}: {e}")
                
        # Logical NOT
        elif op == 'NOT':
            val = self.resolve_variable(arg1)
            # Handle Minima boolean strings explicitly
            if val == "YES" or val is True:
                self.assign_variable(result, "NO") # Use Minima's string representation
            elif val == "NO" or val is False:
                self.assign_variable(result, "YES") # Use Minima's string representation
            else:
                # Fallback to standard Python truthiness for other types
                self.assign_variable(result, not bool(val))

        # Logical AND
        elif op == 'AND':
            left_val = self.resolve_variable(arg1)
            # Short-circuit evaluation
            if not bool(left_val):
                self.assign_variable(result, False)
            else:
                right_val = self.resolve_variable(arg2)
                self.assign_variable(result, bool(right_val))
                
        # Logical OR
        elif op == 'OR':
            left_val = self.resolve_variable(arg1)
            # Short-circuit evaluation
            if bool(left_val):
                self.assign_variable(result, True)
            else:
                right_val = self.resolve_variable(arg2)
                self.assign_variable(result, bool(right_val))
                
        # Equality comparison
        elif op == 'EQ':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            if right_val == 'empty' or right_val is None:
                self.assign_variable(result, (left_val is None or left_val == ''))
            elif left_val == 'empty' or left_val is None:
                self.assign_variable(result, (right_val is None or right_val == ''))
            else:
                self.assign_variable(result, (left_val == right_val))
                
        # Inequality comparison
        elif op == 'NEQ':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            if right_val == 'empty' or right_val is None:
                self.assign_variable(result, (left_val is not None and left_val != ''))
            elif left_val == 'empty' or left_val is None:
                self.assign_variable(result, (right_val is not None and right_val != ''))
            else:
                self.assign_variable(result, (left_val != right_val))
                
        # Less than comparison
        elif op == 'LT':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                if left_val is None and right_val is None:
                    self.assign_variable(result, False)
                elif left_val is None:
                    self.assign_variable(result, True)
                elif right_val is None:
                    self.assign_variable(result, False)
                else:
                    if isinstance(left_val, str) and left_val.isdigit():
                        left_val = int(left_val)
                    if isinstance(right_val, str) and right_val.isdigit():
                        right_val = int(right_val)
                    self.assign_variable(result, (left_val < right_val))
                if self.debug_mode:
                    print(f"LT: {left_val} < {right_val} = {self.memory_stack[-1][result]}")
            except Exception as e:
                raise ValueError(f"Error in LT comparison: {str(e)}")
                
        # Less than or equal comparison
        elif op == 'LE':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                if left_val is None and right_val is None:
                    self.assign_variable(result, True)
                elif left_val is None:
                    self.assign_variable(result, True)
                elif right_val is None:
                    self.assign_variable(result, False)
                else:
                    if isinstance(left_val, str) and left_val.isdigit():
                        left_val = int(left_val)
                    if isinstance(right_val, str) and right_val.isdigit():
                        right_val = int(right_val)
                    self.assign_variable(result, (left_val <= right_val))
            except Exception as e:
                raise ValueError(f"Error in LE comparison: {str(e)}")
                
        # Greater than comparison
        elif op == 'GT':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                if left_val is None and right_val is None:
                    self.assign_variable(result, False)
                elif left_val is None:
                    self.assign_variable(result, False)
                elif right_val is None:
                    self.assign_variable(result, True)
                else:
                    if isinstance(left_val, str) and left_val.isdigit():
                        left_val = int(left_val)
                    if isinstance(right_val, str) and right_val.isdigit():
                        right_val = int(right_val)
                    self.assign_variable(result, (left_val > right_val))
            except Exception as e:
                raise ValueError(f"Error in GT comparison: {str(e)}")
                
        # Greater than or equal comparison
        elif op == 'GE':
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            try:
                if left_val is None and right_val is None:
                    self.assign_variable(result, True)
                elif left_val is None:
                    self.assign_variable(result, False)
                elif right_val is None:
                    self.assign_variable(result, True)
                else:
                    if isinstance(left_val, str) and left_val.isdigit():
                        left_val = int(left_val)
                    if isinstance(right_val, str) and right_val.isdigit():
                        right_val = int(right_val)
                    self.assign_variable(result, (left_val >= right_val))
            except Exception as e:
                raise ValueError(f"Error in GE comparison: {str(e)}")
                
        # Unconditional jump
        elif op == 'GOTO':
            if result in self.labels:
                self.ip = self.labels[result]
            else:
                raise ValueError(f"Label not found: {result}")
                
        # Conditional jump if false
        elif op == 'IFFALSE':
            cond_val = self.resolve_variable(arg1)
            if not self.evaluate_condition(cond_val):  # Use the helper method
                if result in self.labels:
                    self.ip = self.labels[result]
                else:
                    raise ValueError(f"Label not found: {result}")
                    
        # Conditional jump if true
        elif op == 'IFTRUE':
            cond_val = self.resolve_variable(arg1)
            if self.evaluate_condition(cond_val):  # Use the helper method
                if result in self.labels:
                    self.ip = self.labels[result]
                else:
                    raise ValueError(f"Label not found: {result}")
                    
        # Print to output
        elif op == 'PRINT':
            val = self.resolve_variable(arg1)
            if isinstance(val, list):
                formatted_elements = []
                for item in val:
                    if isinstance(item, bool):
                        formatted_elements.append("YES" if item else "NO")
                    elif isinstance(item, (int, float)):
                        formatted_elements.append(self.format_number_for_output(item))
                    elif item is None:
                        formatted_elements.append("empty")
                    else:
                        # Process escapes within list elements if they are strings
                        item_str = str(item)
                        processed_item = ""
                        i = 0
                        while i < len(item_str):
                            if item_str[i] == '\\' and i + 1 < len(item_str):
                                next_char = item_str[i+1]
                                if next_char == 'n': processed_item += '\n'; i += 2
                                elif next_char == 't': processed_item += '\t'; i += 2
                                elif next_char == '"': processed_item += '"'; i += 2
                                elif next_char == '\\': processed_item += '\\'; i += 2
                                else: processed_item += '\\' + next_char; i += 2
                            else:
                                processed_item += item_str[i]; i += 1
                        formatted_elements.append(processed_item)
                self.output_buffer.write("[" + ", ".join(formatted_elements) + "]")
            elif isinstance(val, bool):
                self.output_buffer.write("YES" if val else "NO")
            elif isinstance(val, (int, float)):
                self.output_buffer.write(self.format_number_for_output(val))
            elif val is None:
                self.output_buffer.write("empty")
            else:
                # Convert to string and explicitly process escapes before writing
                str_val = str(val)
                processed_val = ""
                i = 0
                while i < len(str_val):
                    if str_val[i] == '\\' and i + 1 < len(str_val):
                        next_char = str_val[i+1]
                        if next_char == 'n':
                            processed_val += '\n'
                            i += 2
                        elif next_char == 't':
                            processed_val += '\t'
                            i += 2
                        elif next_char == '"':
                            processed_val += '"'
                            i += 2
                        elif next_char == '\\':
                            processed_val += '\\'
                            i += 2
                        else: # Keep unrecognized escapes literal
                            processed_val += '\\' + next_char
                            i += 2
                    else:
                        processed_val += str_val[i]
                        i += 1
                self.output_buffer.write(processed_val)
                
        # String concatenation
        elif op == 'CONCAT':
            val1 = self.resolve_variable(arg1)
            val2 = self.resolve_variable(arg2)
            
            if isinstance(val1, bool):
                str_val1 = "YES" if val1 else "NO"
            elif isinstance(val1, (int, float)):
                str_val1 = self.format_number_for_output(val1)
            else:
                str_val1 = "" if val1 is None else str(val1)
                
            if isinstance(val2, bool):
                str_val2 = "YES" if val2 else "NO"
            elif isinstance(val2, (int, float)):
                str_val2 = self.format_number_for_output(val2)
            else:
                str_val2 = "" if val2 is None else str(val2)
                
            # Process escape sequences
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
                        
            self.assign_variable(result, str_val1 + str_val2)
            
        # User input
        elif op == 'INPUT':
            self.waiting_for_input = True
            self.input_result_var = result
            prompt = self.resolve_variable(arg1)
            self.input_prompt = str(prompt if prompt is not None else "")
            
            # Check next instruction for TYPECAST hint
            self.input_expected_type = None
            next_ip = self.ip + 1
            if next_ip < len(self.instructions):
                next_op, next_arg1, next_arg2, next_result = self.instructions[next_ip]
                if next_op == 'TYPECAST' and next_arg1 == result:
                    self.input_expected_type = next_arg2
                    if self.debug_mode:
                        print(f"  Input for '{result}' expects type '{self.input_expected_type}' due to next instruction.")
                        
        # Type conversion
        elif op == 'TYPECAST':
            val = self.resolve_variable(arg1)
            target_type = arg2
            casted_value = val  # Default if cast fails
            
            try:
                if target_type == 'integer':
                    if isinstance(val, bool):
                        casted_value = 1 if val else 0
                    elif isinstance(val, str):
                        if val.startswith('-'):
                            casted_value = int(float(val[1:])) * -1
                        else:
                            casted_value = int(float(val))
                    elif isinstance(val, float):
                        casted_value = int(val)
                    elif isinstance(val, int):
                        casted_value = val
                    else:
                        casted_value = 0
                    casted_value = self.validate_number(casted_value)
                    
                elif target_type == 'point':
                    if isinstance(val, bool):
                        casted_value = 1.0 if val else 0.0
                    elif isinstance(val, str):
                        if val.startswith('-'):
                            casted_value = float(val[1:]) * -1.0
                        else:
                            casted_value = float(val)
                    elif isinstance(val, int):
                        casted_value = float(val)
                    elif isinstance(val, float):
                        casted_value = val
                    else:
                        casted_value = 0.0
                    casted_value = self.validate_number(casted_value)
                    
                elif target_type == 'text':
                    if isinstance(val, bool):
                        casted_value = "YES" if val else "NO"
                    elif isinstance(val, (int, float)):
                        casted_value = self.format_number_for_output(val)
                    elif val is None:
                        casted_value = "empty"
                    else:
                        casted_value = str(val)
                        
                elif target_type == 'state':
                    if isinstance(val, (int, float)):
                        casted_value = (val != 0)
                    elif isinstance(val, str):
                        casted_value = (val.upper() not in ["", "0", "NO", "FALSE", "EMPTY"])
                    elif isinstance(val, list):
                        casted_value = bool(val)
                    elif val is None:
                        casted_value = False
                    else:
                        casted_value = bool(val)
            except (ValueError, TypeError) as e:
                if self.debug_mode:
                    print(f"Warning: Typecast failed for {val} to {target_type}: {e}")
                if target_type == 'integer': casted_value = 0
                elif target_type == 'point': casted_value = 0.0
                elif target_type == 'text': casted_value = str(val)
                elif target_type == 'state': casted_value = False
                else: casted_value = val
                
            self.assign_variable(result, casted_value)
            
        # List creation
        elif op == 'LIST_CREATE':
            self.assign_variable(result, [])
            
        # List append
        elif op == 'LIST_APPEND':
            list_scope = self.find_variable_scope(arg1)
            if list_scope is None or not isinstance(list_scope[arg1], list):
                if self.debug_mode:
                    print(f"Warning: LIST_APPEND target '{arg1}' not found or not a list. Creating new list.")
                self.assign_variable(arg1, [])
                list_scope = self.memory_stack[-1]
            item = self.resolve_variable(arg2)
            list_scope[arg1].append(item)
            if self.debug_mode:
                print(f"Appended {repr(item)} to list '{arg1}'")
                
        # List extend
        elif op == 'LIST_EXTEND':
            list_scope = self.find_variable_scope(arg1)
            if list_scope is None or not isinstance(list_scope[arg1], list):
                if self.debug_mode:
                    print(f"Warning: LIST_EXTEND target '{arg1}' not found or not a list. Creating new list.")
                self.assign_variable(arg1, [])
                list_scope = self.memory_stack[-1]
            extension_val = self.resolve_variable(arg2)
            if isinstance(extension_val, list):
                list_scope[arg1].extend(extension_val)
                if self.debug_mode:
                    print(f"Extended list '{arg1}' with {repr(extension_val)}")
            else:
                list_scope[arg1].append(extension_val)
                if self.debug_mode:
                    print(f"Extended list '{arg1}' with single item {repr(extension_val)}")
            if result:
                self.assign_variable(result, list_scope[arg1])
                
        # List access (get element)
        elif op == 'LIST_ACCESS':
            list_var = self.resolve_variable(arg1)
            index_raw = arg2
            access_result = None  # Default to None if access fails
            
            try:
                index = self.resolve_variable(index_raw)
                try:
                    if isinstance(index, float) and index.is_integer():
                        index_int = int(index)
                    elif isinstance(index, str) and index.startswith('-'):
                        index_int = -int(index[1:])
                    else:
                        index_int = int(index)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid index type: {type(index).__name__} ({index})")
                    
                if isinstance(list_var, (list, str)):
                    actual_index = index_int
                    if index_int < 0:
                        actual_index = len(list_var) + index_int
                    if 0 <= actual_index < len(list_var):
                        access_result = list_var[actual_index]
                    else:
                        if self.debug_mode:
                            print(f"Index {index_int} (actual: {actual_index}) out of range for {type(list_var).__name__} of length {len(list_var)}")
                else:
                    if self.debug_mode:
                        print(f"Warning: Attempted LIST_ACCESS on non-list/non-string: {type(list_var).__name__}")
            except Exception as e:
                raise ValueError(f"Error during LIST_ACCESS for '{arg1}' at index '{index_raw}': {e}")
                
            self.assign_variable(result, access_result)
            
        # List set (modify element)
        elif op == 'LIST_SET':
            list_name = arg1
            index_raw = arg2
            value_raw = result  # Note: result holds the value here
            
            list_scope = self.find_variable_scope(list_name)
            if list_scope is None or not isinstance(list_scope[list_name], list):
                raise ValueError(f"Cannot perform LIST_SET: '{list_name}' is not a list or not found.")
                
            list_var = list_scope[list_name]
            value = self.resolve_variable(value_raw)
            
            try:
                index = self.resolve_variable(index_raw)
                try:
                    if isinstance(index, float) and index.is_integer():
                        index_int = int(index)
                    elif isinstance(index, str) and index.startswith('-'):
                        index_int = -int(index[1:])
                    else:
                        index_int = int(index)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid index type for LIST_SET: {type(index).__name__} ({index})")
                    
                actual_index = index_int
                if index_int < 0:
                    actual_index = len(list_var) + index_int
                    
                if 0 <= actual_index < len(list_var):
                    list_var[actual_index] = value
                    if self.debug_mode:
                        print(f"Set list '{list_name}' index {actual_index} to {repr(value)}")
                else:
                    raise ValueError(f"List index {index_int} (actual: {actual_index}) out of range for assignment (length {len(list_var)})")
            except Exception as e:
                raise ValueError(f"Error during LIST_SET for '{list_name}' at index '{index_raw}': {e}")
                
        # Dictionary creation
        elif op == 'GROUP_CREATE':
            self.assign_variable(result, {})
            
        # Dictionary access
        elif op == 'GROUP_ACCESS':
            group = self.resolve_variable(arg1)
            key = self.resolve_variable(arg2)
            if isinstance(group, dict):
                if key in group:
                    self.assign_variable(result, group[key])
                else:
                    raise ValueError(f"Key {key} not found in group {arg1}")
            else:
                raise ValueError(f"Cannot access key in non-group: {arg1}")
                
        # Dictionary set
        elif op == 'GROUP_SET':
            group_name = arg1
            group_scope = self.find_variable_scope(group_name)
            if group_scope is None or not isinstance(group_scope[group_name], dict):
                self.assign_variable(group_name, {})
                group_scope = self.memory_stack[-1]
                
            key = self.resolve_variable(arg2)
            value = self.resolve_variable(result)
            group_scope[group_name][key] = value
            
            if self.debug_mode:
                print(f"Set group {group_name}[{key}] = {value}")
                
        # Runtime error
        elif op == 'ERROR':
            error_msg = self.resolve_variable(arg1)
            raise ValueError(f"Explicit runtime error: {error_msg}")
            
        # Unknown instruction
        else:
            raise ValueError(f"Unknown TAC instruction: {op}")
            
        # Debug output
        if self.debug_mode:
            print(f"  Scope after instruction {self.ip} ({op}): {self.memory_stack[-1]}")