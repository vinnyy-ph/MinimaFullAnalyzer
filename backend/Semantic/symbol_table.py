# backend/Semantic/symbol_table.py

class Symbol:
    def __init__(self, name, kind, fixed=False, params=None, line=None, column=None, var_type=None, is_param=False):
        self.name = name
        self.kind = kind # "variable" or "function"
        self.fixed = fixed # Applies only to variables
        self.params = params or [] # For functions
        self.line = line # Line where defined
        self.column = column # Column where defined
        self.var_type = var_type # Inferred or declared type (string like 'integer', 'text', etc.)
        self.is_param = is_param # Flag if this variable is a function parameter

class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.variables = {} # Stores Symbol objects for variables/parameters
        self.functions = {} # Stores Symbol objects for functions

    def define_variable(self, name, fixed=False, line=None, column=None, var_type=None, is_param=False):
        """Defines a variable or parameter in the current scope."""
        # Check for redeclaration in the *current* scope only
        if name in self.variables:
            return None # Indicate error (redeclaration in this scope)

        # Also check if name conflicts with a function in this scope (or globally?)
        # Let's check globally for functions to prevent shadowing issues
        if self.lookup_function(name, check_parents=True):
             # Cannot define variable with the same name as an existing function
             return None # Indicate error

        symbol_obj = Symbol(name, "variable", fixed, line=line, column=column, var_type=var_type, is_param=is_param)
        self.variables[name] = symbol_obj
        return symbol_obj # Return the created Symbol object on success

    def define_function(self, name, params=None, line=None, column=None):
        """Defines a function in the current scope (usually global)."""
        # Check for redeclaration in the *current* scope
        if name in self.functions:
            return None # Indicate error (redeclaration)
        # Check for conflict with variables in the current scope
        if name in self.variables:
             return None # Indicate error (conflict)

        symbol_obj = Symbol(name, "function", fixed=False, params=params or [], line=line, column=column)
        self.functions[name] = symbol_obj
        return symbol_obj # Return the created Symbol object on success

    def lookup_variable(self, name, check_parents=True):
        """Looks up a variable/parameter symbol, checking parent scopes if requested."""
        if name in self.variables:
            return self.variables[name]
        if check_parents and self.parent:
            return self.parent.lookup_variable(name, check_parents=True)
        return None # Not found

    def lookup_function(self, name, check_parents=True):
        """Looks up a function symbol, checking parent scopes if requested."""
        # Functions are typically defined globally, but allow lookup through parents
        if name in self.functions:
            return self.functions[name]
        if check_parents and self.parent:
            return self.parent.lookup_function(name, check_parents=True)
        return None # Not found

    def find_variable_scope(self, name):
        """Finds the specific scope containing the variable and returns (scope, symbol)."""
        if name in self.variables:
            return (self, self.variables[name])
        if self.parent:
            return self.parent.find_variable_scope(name)
        return (None, None) # Not found in any scope
