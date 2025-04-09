from io import StringIO

class TACInterpreter:
    def __init__(self):
        self.memory = {}
        self.functions = {}
        self.call_stack = []
        self.ip = 0
        self.param_stack = []
        self.output_buffer = StringIO()
        self.instructions = []
        self.labels = {}
        self.function_bodies = {}
        self.global_memory = {}

    def reset(self):
        self.memory = {}
        self.functions = {}
        self.call_stack = []
        self.ip = 0
        self.param_stack = []
        self.output_buffer = StringIO()
        self.function_bodies = {}
        self.global_memory = {}

    def load(self, instructions):
        self.reset()
        self.instructions = instructions

        current_function = None
        current_function_body = []
        for i, (op, arg1, arg2, result) in enumerate(instructions):
            if op == 'FUNCTION':
                current_function = arg1
                current_function_body = []
                self.functions[current_function] = result
            elif op == 'LABEL':
                self.labels[result] = i

            if current_function:
                current_function_body.append((op, arg1, arg2, result))

            if op == 'RETURN' or op == 'FUNCTION':
                if current_function:
                    self.function_bodies[current_function] = current_function_body
                    current_function = None
                    current_function_body = []

        return self

    def get_value(self, arg):
        if arg is None:
            return None
        if isinstance(arg, str) and arg in self.memory:
            return self.memory[arg]
        return arg

    def run(self):
        self.ip = 0
        while 0 <= self.ip < len(self.instructions):
            op, arg1, arg2, result = self.instructions[self.ip]
            self.execute_instruction(op, arg1, arg2, result)
            if op not in ('GOTO', 'IFFALSE', 'IFTRUE', 'RETURN', 'CALL'):
                self.ip += 1
        return self.output_buffer.getvalue()

    def execute_instruction(self, op, arg1, arg2, result):
        if op == 'CALL':
            # arg1: function name, arg2: number of params, result: return var
            if arg1 in self.functions:
                context = {
                    'ip': self.ip + 1,
                    'memory': dict(self.memory),
                    'return_var': result
                }
                func_label = self.functions[arg1]
                if func_label in self.labels:
                    self.call_stack.append(context)
                    self.ip = self.labels[func_label]
                else:
                    raise ValueError(f"Function label not found: {func_label}")

                # collect param values
                new_params = []
                param_count = arg2 if isinstance(arg2, int) else 0
                if param_count > 0:
                    for i in range(param_count):
                        for p_idx, p_val in self.param_stack:
                            if p_idx == i:
                                new_params.append((i, p_val))
                                break
                self.param_stack = new_params
            else:
                raise ValueError(f"Function not defined: {arg1}")

        elif op == 'RETURN':
            if self.call_stack:
                return_val = self.get_value(arg1)
                old_ctx = self.call_stack.pop()
                if old_ctx['return_var']:
                    old_ctx['memory'][old_ctx['return_var']] = return_val
                self.memory = old_ctx['memory']
                self.ip = old_ctx['ip']
            else:
                # If we have no call stack, just end program
                self.ip = len(self.instructions)

        elif op == 'FUNCTION':
            # no-op
            pass

        elif op == 'LABEL':
            # no-op
            pass

        elif op == 'PARAM':
            val = self.get_value(arg1)
            self.param_stack.append((result, val))

        elif op == 'ASSIGN':
            self.memory[result] = self.get_value(arg1)

        elif op == 'ADD':
            self.memory[result] = self.get_value(arg1) + self.get_value(arg2)

        elif op == 'SUB':
            self.memory[result] = self.get_value(arg1) - self.get_value(arg2)

        elif op == 'MUL':
            self.memory[result] = self.get_value(arg1) * self.get_value(arg2)

        elif op == 'DIV':
            denom = self.get_value(arg2)
            if denom == 0:
                raise ValueError("Division by zero")
            self.memory[result] = self.get_value(arg1) / denom

        elif op == 'MOD':
            denom = self.get_value(arg2)
            if denom == 0:
                raise ValueError("Modulo by zero")
            self.memory[result] = self.get_value(arg1) % denom

        elif op == 'NEG':
            self.memory[result] = -self.get_value(arg1)

        elif op == 'NOT':
            self.memory[result] = not self.get_value(arg1)

        elif op == 'AND':
            self.memory[result] = self.get_value(arg1) and self.get_value(arg2)

        elif op == 'OR':
            self.memory[result] = self.get_value(arg1) or self.get_value(arg2)

        elif op == 'EQ':
            self.memory[result] = (self.get_value(arg1) == self.get_value(arg2))

        elif op == 'NEQ':
            self.memory[result] = (self.get_value(arg1) != self.get_value(arg2))

        elif op == 'LT':
            self.memory[result] = self.get_value(arg1) < self.get_value(arg2)

        elif op == 'LE':
            self.memory[result] = self.get_value(arg1) <= self.get_value(arg2)

        elif op == 'GT':
            self.memory[result] = self.get_value(arg1) > self.get_value(arg2)

        elif op == 'GE':
            self.memory[result] = self.get_value(arg1) >= self.get_value(arg2)

        elif op == 'GOTO':
            if result in self.labels:
                self.ip = self.labels[result]
            else:
                raise ValueError(f"Label not found: {result}")

        elif op == 'IFFALSE':
            cond = self.get_value(arg1)
            if not cond:
                if result in self.labels:
                    self.ip = self.labels[result]
                else:
                    raise ValueError(f"Label not found: {result}")
            else:
                self.ip += 1

        elif op == 'IFTRUE':
            cond = self.get_value(arg1)
            if cond:
                if result in self.labels:
                    self.ip = self.labels[result]
                else:
                    raise ValueError(f"Label not found: {result}")
            else:
                self.ip += 1

        elif op == 'PRINT':
            val = self.get_value(arg1)
            self.output_buffer.write(str(val) + "\n")

        elif op == 'INPUT':
            prompt = self.get_value(arg1)
            if not prompt:
                prompt = "Enter value"
            # For a real console you might do input(), but here we set a default
            self.memory[result] = "USERINPUT"

        else:
            raise ValueError(f"Unknown op: {op}")
