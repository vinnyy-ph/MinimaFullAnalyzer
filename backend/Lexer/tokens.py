class Token:
    def __init__(self, type, value, line, column, error=None):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
        self.error = error 
        
    def __str__(self):
        if self.error:
            return f"Token({self.type}, {self.value}, {self.line}, {self.column}, {self.error})"
        else:
            return f"Token({self.type}, {self.value}, {self.line}, {self.column})"