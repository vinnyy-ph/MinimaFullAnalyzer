class Token:
    def __init__(self, type, value, line, column, error=None, warning=None):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
        self.error = error
        self.warning = warning
        
    def __str__(self):
        if self.error:
            return f"Token({self.type}, {self.value}, {self.line}, {self.column}, {self.error})"
        elif self.warning:
            return f"Token({self.type}, {self.value}, {self.line}, {self.column}, warning: {self.warning})"
        else:
            return f"Token({self.type}, {self.value}, {self.line}, {self.column})"