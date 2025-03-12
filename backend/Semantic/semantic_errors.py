# semantic_errors.py

class SemanticError(Exception):
    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.message)

    def to_dict(self):
        return {
            'message': self.message,
            'line': self.line,
            'column': self.column,
            'type': 'semantic'
        }

class UndefinedIdentifierError(SemanticError):
    def __init__(self, identifier, line=None, column=None):
        message = f"Undefined identifier '{identifier}'"
        super().__init__(message, line, column)

class RedeclarationError(SemanticError):
    def __init__(self, identifier, line=None, column=None):
        message = f"Variable '{identifier}' is already declared in the current scope"
        super().__init__(message, line, column)

class FixedVarReassignmentError(SemanticError):
    def __init__(self, identifier, line=None, column=None):
        message = f"Cannot reassign fixed variable '{identifier}'"
        super().__init__(message, line, column)

class FunctionNotDefinedError(SemanticError):
    def __init__(self, function_name, line=None, column=None):
        message = f"Function '{function_name}' is not defined"
        super().__init__(message, line, column)

class ParameterMismatchError(SemanticError):
    def __init__(self, function_name, expected, got, line=None, column=None):
        message = (
            f"Function '{function_name}' expects {expected} argument(s) but got {got}"
        )
        super().__init__(message, line, column)
