class LexerError:
    def __init__(self, message, line, column, category):
        self.message = message
        self.line = line
        self.column = column
        self.category = category
        self.is_warning = False  # Flag to distinguish errors from warnings

    def to_dict(self):
        return {
            'message': self.message,
            'line': self.line,
            'column': self.column,
            'category': self.category,
            'is_warning': self.is_warning
        }

class LexerWarning(LexerError):
    def __init__(self, message, line, column, category="Style Warning"):
        super().__init__(message, line, column, category)
        self.is_warning = True  # Mark as a warning, not an error

# specific error categories
class InvalidIdentifierError(LexerError):
    def __init__(self, value, line, column, message=None):
        if not message:
            message = f"Invalid identifier: '{value}'"
        super().__init__(message, line, column, 'Invalid Identifier')

class InvalidSymbolError(LexerError):
    def __init__(self, value, line, column):
        message = f"Invalid symbol: '{value}'"
        super().__init__(message, line, column, 'Invalid Symbol')

class InvalidIntegerError(LexerError):
    def __init__(self, message, line, column):
        super().__init__(message, line, column, 'Invalid Integer Literal')

class InvalidPointError(LexerError):
    def __init__(self, message, line, column):
        super().__init__(message, line, column, 'Invalid Point Literal')