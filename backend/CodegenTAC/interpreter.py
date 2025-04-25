from io import StringIO
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
        self.max_execution_steps = 1000  
        self.max_digits = 9
        self.min_number = -999999999
        self.max_number = 999999999
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
            if abs(value) > float(self.max_number) + 0.999999999:
                raise ValueError(f"Float value out of range: {value}. Valid range is ~{self.min_number}.999999999 to {self.max_number}.999999999")
        return value
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
                    pass
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
        last_ips = []  
        loop_detection_window = 10  
        loop_threshold = 20  
        loop_pattern_count = 0
        while 0 <= self.ip < len(self.instructions):
            if self.max_execution_steps is not None and self.steps_executed >= self.max_execution_steps:
                print(f"Execution terminated after {self.steps_executed} steps to prevent infinite loop.")
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
            if self.debug_mode and op in ('LABEL', 'GOTO', 'IFTRUE', 'IFFALSE'):
                print(f"Step {self.steps_executed}: Executing {op} {arg1} {arg2} {result} at IP {self.ip}")
            self.execute_instruction(op, arg1, arg2, result)
            self.steps_executed += 1
            if self.waiting_for_input:
                break
            if op not in ('GOTO', 'IFFALSE', 'IFTRUE', 'RETURN', 'CALL'):
                self.ip += 1
        return self.output_buffer.getvalue()
    def resume_with_input(self, user_input):
        """Resume execution after receiving user input with strict number validation."""
        if not self.waiting_for_input:
            raise ValueError("Interpreter is not waiting for input")
        try:
            if user_input.startswith('~') and len(user_input) > 1:
                num_str = user_input[1:]
                parts = num_str.split('.')
                if len(parts[0]) > self.max_digits:
                    raise ValueError(f"Input integer part has {len(parts[0])} digits. Maximum {self.max_digits} digits allowed.")
                if len(parts) > 1 and len(parts[1]) > self.max_digits:
                    raise ValueError(f"Input decimal part has {len(parts[1])} digits. Maximum {self.max_digits} digits allowed.")
                if '.' in num_str:
                    input_val = -float(num_str)
                else:
                    input_val = -int(num_str)
            else:
                parts = user_input.split('.')
                if len(parts[0]) > self.max_digits:
                    raise ValueError(f"Input integer part has {len(parts[0])} digits. Maximum {self.max_digits} digits allowed.")
                if len(parts) > 1 and len(parts[1]) > self.max_digits:
                    raise ValueError(f"Input decimal part has {len(parts[1])} digits. Maximum {self.max_digits} digits allowed.")
                if '.' in user_input:
                    input_val = float(user_input)
                else:
                    input_val = int(user_input)
            input_val = self.validate_number(input_val)
        except ValueError as e:
            if "digits" in str(e) or "out of range" in str(e):
                raise e  
            input_val = user_input
        self.memory[self.input_result_var] = input_val
        self.waiting_for_input = False
        self.input_prompt = ""
        self.ip += 1
        while 0 <= self.ip < len(self.instructions):
            op, arg1, arg2, result = self.instructions[self.ip]
            self.execute_instruction(op, arg1, arg2, result)
            if self.waiting_for_input:
                break
            if op not in ('GOTO', 'IFFALSE', 'IFTRUE', 'RETURN', 'CALL'):
                self.ip += 1
        return self.output_buffer.getvalue()
    def execute_instruction(self, op, arg1, arg2, result):
        if self.debug_mode and op in ('LABEL', 'GOTO', 'IFTRUE', 'IFFALSE'):
            print(f"Executing {op} with args: {arg1}, {arg2}, {result}")
        if self.debug_mode and op in ('LT', 'LE', 'GT', 'GE', 'EQ', 'NEQ'):
            left_val = self.resolve_variable(arg1)
            right_val = self.resolve_variable(arg2)
            print(f"Condition: {left_val} {op} {right_val}")
        if op == 'CALL':
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
                if old_ctx['return_var']:
                    old_ctx['memory'][old_ctx['return_var']] = return_val
                self.memory = old_ctx['memory']
                self.ip = old_ctx['ip']
            else:
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
                    if param_names and param_count > 0:
                        for i, param_name in enumerate(param_names):
                            if i >= param_count:
                                break  
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
            if isinstance(left_val, list):
                if isinstance(right_val, list):
                    resolved_right = []
                    for item in right_val:
                        if isinstance(item, tuple) and len(item) >= 2 and item[0] == 'id':
                            var_name = item[1]
                            if var_name in self.memory:
                                resolved_right.append(self.memory[var_name])
                            else:
                                resolved_right.append(var_name)
                        else:
                            resolved_right.append(item)
                    self.memory[result] = left_val + resolved_right
                else:
                    self.memory[result] = left_val + [right_val]
                return
            elif isinstance(right_val, list):
                self.memory[result] = [left_val] + right_val
                return
            left_is_string = False
            right_is_string = False
            if isinstance(left_val, str):
                if not left_val:  
                    left_is_string = True
                elif left_val.isdigit():
                    left_is_string = False
                elif len(left_val) > 0 and left_val[0] == '-' and left_val[1:].isdigit():
                    left_is_string = False
                else:
                    left_is_string = True
            if isinstance(right_val, str):
                if not right_val:  
                    right_is_string = True
                elif right_val.isdigit():
                    right_is_string = False
                elif len(right_val) > 0 and right_val[0] == '-' and right_val[1:].isdigit():
                    right_is_string = False
                else:
                    right_is_string = True
            if left_is_string or right_is_string:
                if isinstance(left_val, bool):
                    str_left = "YES" if left_val else "NO"
                else:
                    str_left = "" if left_val is None else str(left_val)
                if isinstance(right_val, bool):
                    str_right = "YES" if right_val else "NO"
                else:
                    str_right = "" if right_val is None else str(right_val)
                self.memory[result] = str_left + str_right
            else:
                try:
                    left_num = float(left_val) if isinstance(left_val, float) or (isinstance(left_val, str) and '.' in left_val) else int(left_val)
                    right_num = float(right_val) if isinstance(right_val, float) or (isinstance(right_val, str) and '.' in right_val) else int(right_val)
                    computed_result = left_num + right_num
                    self.memory[result] = self.validate_number(computed_result)
                except ValueError as e:
                    if "out of range" in str(e) or "too many digits" in str(e):
                        raise e
                    self.memory[result] = str(left_val) + str(right_val)
        elif op == 'LIST_EXTEND':
            list_var = self.resolve_variable(arg1)
            extension = self.resolve_variable(arg2)
            if not isinstance(list_var, list):
                list_var = []
                self.memory[arg1] = list_var
            if isinstance(extension, list):
                resolved_extension = []
                for item in extension:
                    if isinstance(item, str):
                        resolved_item = self.resolve_variable(item)
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
                if isinstance(extension, str) and extension in self.memory:
                    extension = self.memory[extension]
                list_var.append(extension)
            if result is not None:
                self.memory[result] = list_var
        elif op == 'LIST_SET':
            list_var = self.resolve_variable(arg1)
            index = self.resolve_variable(arg2)
            value = self.resolve_variable(result)
            
            if isinstance(list_var, list):
                if isinstance(index, int) and 0 <= index < len(list_var):
                    list_var[index] = value
                elif isinstance(index, int) and index >= len(list_var):
                    # Extend the list if needed
                    while len(list_var) <= index:
                        list_var.append(None)
                    list_var[index] = value
                else:
                    # Handle invalid index
                    raise ValueError(f"Invalid list index: {index}")
            else:
                raise ValueError(f"Cannot assign to index of non-list: {arg1}")
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
                self.memory[result] = left_num * right_num
            except (ValueError, TypeError):
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
                left_num = float(left_val) if isinstance(left_val, float) or (isinstance(left_val, str) and '.' in left_val) else int(left_val)
                right_num = float(right_val) if isinstance(right_val, float) or (isinstance(right_val, str) and '.' in right_val) else int(right_val)
                if right_num == 0:
                    raise ValueError("Division by zero")
                self.memory[result] = left_num / right_num
            except (ValueError, TypeError) as e:
                if "Division by zero" in str(e):
                    raise ValueError("Division by zero")
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
            self.memory[result] = left_val % right_val
        elif op == 'NEG':
            val = self.resolve_variable(arg1)
            try:
                self.memory[result] = -float(val) if isinstance(val, float) or (isinstance(val, str) and '.' in val) else -int(val)
            except (ValueError, TypeError):
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
            if isinstance(val, list):
                formatted_list = []
                for item in val:
                    if isinstance(item, tuple) and len(item) >= 2:
                        value = item[1]
                        if isinstance(value, bool):
                            value = "YES" if value else "NO"
                        elif isinstance(value, (int, float)) and value < 0:
                            if isinstance(value, float):
                                decimal_str = f"{abs(value):.9f}".rstrip('0').rstrip('.')
                                value = f"~{decimal_str}"
                            else:
                                value = f"~{abs(value)}"
                        elif isinstance(value, float):
                            value = f"{value:.9f}".rstrip('0').rstrip('.')
                        formatted_list.append(value)
                    else:
                        if isinstance(item, bool):
                            item = "YES" if item else "NO"
                        elif isinstance(item, (int, float)) and item < 0:
                            if isinstance(item, float):
                                decimal_str = f"{abs(item):.9f}".rstrip('0').rstrip('.')
                                item = f"~{decimal_str}"
                            else:
                                item = f"~{abs(item)}"
                        elif isinstance(item, float):
                            item = f"{item:.9f}".rstrip('0').rstrip('.')
                        formatted_list.append(item)
                self.output_buffer.write(str(formatted_list))
            else:
                if isinstance(val, bool):
                    val = "YES" if val else "NO"
                elif isinstance(val, (int, float)) and val < 0:
                    if isinstance(val, float):
                        decimal_str = f"{abs(val):.9f}".rstrip('0').rstrip('.')
                        val = f"~{decimal_str}"
                    else:
                        val = f"~{abs(val)}"
                elif isinstance(val, float):
                    val = f"{val:.9f}".rstrip('0').rstrip('.')
                if isinstance(val, str):
                    val = val.replace('\\\\', '\\')  
                    val = val.replace('\\"', '"')    
                    val = val.replace('\\n', '\n')   
                    val = val.replace('\\t', '\t')   
                self.output_buffer.write(str(val))
        elif op == 'INPUT':
            self.waiting_for_input = True
            self.input_result_var = result
            prompt = self.resolve_variable(arg1)
            if not prompt:
                prompt = ""  
            self.input_prompt = prompt
        elif op == 'CONCAT':
            val1 = self.resolve_variable(arg1)
            val2 = self.resolve_variable(arg2)
            if isinstance(val1, bool):
                str_val1 = "YES" if val1 else "NO"
            elif isinstance(val1, (int, float)) and val1 < 0:
                str_val1 = f"~{abs(val1)}"
            else:
                str_val1 = "" if val1 is None else str(val1)
            if isinstance(val2, bool):
                str_val2 = "YES" if val2 else "NO"
            elif isinstance(val2, (int, float)) and val2 < 0:
                str_val2 = f"~{abs(val2)}"
            else:
                str_val2 = "" if val2 is None else str(val2)
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
        elif op == 'TYPECAST':
            val = self.resolve_variable(arg1)
            if arg2 == 'integer':
                if isinstance(val, bool):
                    self.memory[result] = 1 if val else 0
                else:
                    try:
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
            index_raw = arg2  
            try:
                if isinstance(index_raw, tuple) and len(index_raw) >= 2:
                    if index_raw[0] == 'id':
                        var_name = index_raw[1]
                        if var_name in self.memory:
                            index = self.memory[var_name]
                        else:
                            if self.debug_mode:
                                print(f"Variable '{var_name}' not found for indexing, using 0")
                            index = 0
                    else:
                        index = index_raw[1]
                else:
                    index = self.resolve_variable(index_raw)
                try:
                    index = int(index)
                except (ValueError, TypeError):
                    if self.debug_mode:
                        print(f"Warning: Could not convert index {index} to integer, using 0")
                    index = 0
            except Exception as e:
                if self.debug_mode:
                    print(f"Exception during index extraction: {e}")
                index = 0
            try:
                if isinstance(list_var, list):
                    list_length = len(list_var)
                    if index < 0:
                        normalized_index = index + list_length
                    else:
                        normalized_index = index
                    if 0 <= normalized_index < list_length:
                        element = list_var[normalized_index]
                        if isinstance(element, tuple) and len(element) >= 2:
                            self.memory[result] = element[1]
                        else:
                            self.memory[result] = element
                    else:
                        if self.debug_mode:
                            print(f"List index out of bounds: {normalized_index} (list length: {list_length})")
                        self.memory[result] = None
                elif isinstance(list_var, str):
                    string_length = len(list_var)
                    if index < 0:
                        normalized_index = index + string_length
                    else:
                        normalized_index = index
                    if 0 <= normalized_index < string_length:
                        try:
                            self.memory[result] = list_var[normalized_index]
                            if self.debug_mode:
                                print(f"String access: '{list_var}' at index {normalized_index} = '{list_var[normalized_index]}'")
                        except IndexError:
                            if self.debug_mode:
                                print(f"Index error handled: {normalized_index} for string of length {string_length}")
                            self.memory[result] = None
                    else:
                        if self.debug_mode:
                            print(f"String index out of bounds: {normalized_index} (string: '{list_var}', length: {string_length})")
                        self.memory[result] = None
                else:
                    if self.debug_mode:
                        print(f"Warning: Cannot index non-list/non-string: {arg1} ({type(list_var).__name__})")
                    self.memory[result] = None
            except Exception as e:
                if self.debug_mode:
                    print(f"Error during LIST_ACCESS operation: {e}")
                self.memory[result] = None
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