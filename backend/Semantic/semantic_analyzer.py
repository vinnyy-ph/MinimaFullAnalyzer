from lark import Transformer, Token
from .semantic_errors import UndefinedIdentifierError
from .symbol_table import SymbolTable

class SemanticAnalyzer(Transformer):
    def __init__(self):
        super().__init__()
        self.symbol_table = SymbolTable()
        self.errors = []

    # Process variable declarations (rule: varlist_declaration)
    def varlist_declaration(self, items):
        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER":
                identifier = item.value
                self.symbol_table.add(identifier, {"type": "variable"})
        return items

    # Process fixed declarations (rule: fixed_declaration)
    def fixed_declaration(self, items):
        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER":
                identifier = item.value
                self.symbol_table.add(identifier, {"type": "variable", "fixed": True})
        return items

    # Process function definitions (rule: func_definition)
    def func_definition(self, items):
        # The first IDENTIFIER encountered is the function name.
        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER":
                identifier = item.value
                self.symbol_table.add(identifier, {"type": "function"})
                break
        # Create a new scope for function parameters and body.
        self.symbol_table.enter_scope()
        # Process children (parameters and body)
        # After processing, exit the function scope.
        self.symbol_table.exit_scope()
        return items

    # Check for identifier usage (rule: id_usage)
    def id_usage(self, items):
        # Debug: print when id_usage is invoked
        print("id_usage called with items:", items)
        identifier_token = items[0]
        if isinstance(identifier_token, Token) and identifier_token.type == "IDENTIFIER":
            identifier = identifier_token.value
            if not self.symbol_table.exists(identifier):
                line = getattr(identifier_token, 'line', None)
                column = getattr(identifier_token, 'column', None)
                error = UndefinedIdentifierError(identifier, line, column)
                self.errors.append(error)
        return items

    # Pass-through for other rules.
    def declaration(self, items):
        return items

    def var_assign(self, items):
        return items

    def statement(self, items):
        return items

    def expression(self, items):
        return items

    def program(self, items):
        return items