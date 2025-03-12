# symbol_table.py

class SymbolTable:
    def __init__(self):
        # Initialize with a global scope dictionary
        self.scopes = [{}]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
        else:
            raise Exception("Cannot exit global scope")

    def is_declared_in_current_scope(self, identifier):
        """Return True if 'identifier' is declared in the current (innermost) scope."""
        return identifier in self.scopes[-1]

    def add(self, identifier, info):
        # Add symbol info to the innermost scope dictionary
        self.scopes[-1][identifier] = info

    def exists(self, identifier):
        # Check in all scopes from innermost to outermost
        for scope in reversed(self.scopes):
            if identifier in scope:
                return True
        return False

    def get(self, identifier):
        for scope in reversed(self.scopes):
            if identifier in scope:
                return scope[identifier]
        return None
