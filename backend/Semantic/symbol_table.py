class Symbol:
    def __init__(self, name, kind, fixed=False, params=None, line=None, column=None, var_type=None):
        """
        kind: "variable" or "function"
        fixed: True if declared as fixed (immutable) – applies only to variables.
        params: For functions, a list of parameter names.
        var_type: Possibly store an inferred type of the variable.
        """
        self.name = name
        self.kind = kind
        self.fixed = fixed
        self.params = params or []
        self.line = line
        self.column = column
        self.var_type = var_type
        self.is_parameter = False
        self.initialized = False  # Track if a variable has been initialized

class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.variables = {}
        self.functions = {}

    def define_variable(self, name, fixed=False, line=None, column=None, var_type=None):
        if name in self.variables:
            return False
        self.variables[name] = Symbol(name, "variable", fixed, line=line, column=column, var_type=var_type)
        return True

    def define_function(self, name, params=None, line=None, column=None):
        if name in self.functions:
            return False
        self.functions[name] = Symbol(name, "function", fixed=False, params=params or [], line=line, column=column)
        return True

    def lookup_variable(self, name):
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.lookup_variable(name)
        return None

    def lookup_function(self, name):
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.lookup_function(name)
        return None

    def find_variable_scope(self, name):
        """Find the scope containing the variable and return (scope, symbol)."""
        if name in self.variables:
            return (self, self.variables[name])
        if self.parent:
            return self.parent.find_variable_scope(name)
        return (None, None)
