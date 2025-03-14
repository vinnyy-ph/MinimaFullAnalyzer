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
        message = f"Function '{function_name}' expects {expected} argument(s) but got {got}"
        super().__init__(message, line, column)

class FunctionRedefinedError(SemanticError):
    def __init__(self, function_name, line=None, column=None):
        message = f"Function '{function_name}' is already defined"
        super().__init__(message, line, column)

class ControlFlowError(SemanticError):
    def __init__(self, statement, context, line=None, column=None):
        message = f"'{statement}' statement can only be used inside {context}"
        super().__init__(message, line, column)

class TypeMismatchError(SemanticError):
    def __init__(self, expected, got, context=None, line=None, column=None):
        if context:
            message = f"Expected {expected} type in {context}, but got {got}"
        else:
            message = f"Expected {expected} type, but got {got}"
        super().__init__(message, line, column)

class UnreachableCodeError(SemanticError):
    def __init__(self, line=None, column=None):
        message = "Unreachable code detected"
        super().__init__(message, line, column)

class InvalidGroupAccessError(SemanticError):
    def __init__(self, variable, line=None, column=None):
        message = f"Variable '{variable}' is not a group"
        super().__init__(message, line, column)

class InvalidListAccessError(SemanticError):
    def __init__(self, identifier, line=None, column=None):
        message = f"Error: Variable '{identifier}' is not a list"
        super().__init__(message, line, column)

class InvalidGroupAccessError(SemanticError):
    def __init__(self, identifier, line=None, column=None):
        message = f"Error: Variable '{identifier}' is not a group"
        super().__init__(message, line, column)

class ListIndexOutOfRangeError(SemanticError):
    def __init__(self, identifier, index, line=None, column=None):
        message = f"Error: list index {index} out of range for variable '{identifier}'"
        super().__init__(message, line, column)

class KeyError(SemanticError):
    def __init__(self, group_name, key, line=None, column=None):
        message = f"Key '{key}' not found in group '{group_name}'"
        super().__init__(message, line, column)

class InvalidListOperandError(SemanticError):
    def __init__(self, operator, line=None, column=None):
        message = f"Operator '{operator}' not allowed with list operand"
        super().__init__(message, line, column)