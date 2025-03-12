from lark import Transformer, Token, Tree
from .semantic_errors import UndefinedIdentifierError, RedeclarationError, FixedVarReassignmentError, FunctionNotDefinedError, ParameterMismatchError
from .symbol_table import SymbolTable

class SemanticAnalyzer(Transformer):
    def __init__(self):
        super().__init__()
        self.symbol_table = SymbolTable()
        self.errors = []

    # Process variable declarations (rule: varlist_declaration)
    def varlist_declaration(self, items):
        # items: [VAR, IDENTIFIER, var_init, varlist_tail, SEMICOLON]
        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER":
                identifier = item.value
                # Check if already declared in the current scope
                if self.symbol_table.is_declared_in_current_scope(identifier):
                    self.errors.append(RedeclarationError(identifier, item.line, item.column))
                else:
                    # Mark variable as not fixed and not yet assigned (unless an initializer is present)
                    self.symbol_table.add(identifier, {"type": "variable", "fixed": False, "assigned": False})
        return items

    # Process fixed declarations (rule: fixed_declaration)
    def fixed_declaration(self, items):
        # items: [FIXED, IDENTIFIER, ASSIGN, variable_value, fixed_tail, SEMICOLON]
        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER":
                identifier = item.value
                if self.symbol_table.is_declared_in_current_scope(identifier):
                    self.errors.append(RedeclarationError(identifier, item.line, item.column))
                else:
                    # Fixed variables are assigned at declaration and cannot be changed later.
                    self.symbol_table.add(identifier, {"type": "variable", "fixed": True, "assigned": True})
        return items

    # Process group declarations (optional semantic check)
    def group_declaration(self, items):
        # items: [GROUP, IDENTIFIER, LBRACE, group_members, RBRACE, (optional SEMICOLON)]
        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER":
                identifier = item.value
                if self.symbol_table.is_declared_in_current_scope(identifier):
                    self.errors.append(RedeclarationError(identifier, item.line, item.column))
                else:
                    self.symbol_table.add(identifier, {"type": "group", "members": {}})
        # (Additional checks on duplicate keys inside group_members could be added here.)
        return items

    # Process assignments (rule: var_assign)
    def var_assign(self, items):
        # var_assign: IDENTIFIER group_or_list assign_op variable_value
        identifier_token = items[0]
        if isinstance(identifier_token, Token) and identifier_token.type == "IDENTIFIER":
            identifier = identifier_token.value
            symbol = self.symbol_table.get(identifier)
            if symbol is None:
                self.errors.append(UndefinedIdentifierError(identifier, identifier_token.line, identifier_token.column))
            else:
                if symbol.get("fixed", False):
                    self.errors.append(FixedVarReassignmentError(identifier, identifier_token.line, identifier_token.column))
                else:
                    # Mark variable as assigned after a successful assignment.
                    symbol["assigned"] = True
        return items

    # Process function definitions (rule: func_definition)
    def func_definition(self, items):
        # func_definition: FUNC IDENTIFIER LPAREN param RPAREN LBRACE function_prog RBRACE SEMICOLON?
        func_name = None
        params = []
        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER" and func_name is None:
                func_name = item.value
                # Check for redeclaration in the global scope.
                if self.symbol_table.is_declared_in_current_scope(func_name):
                    self.errors.append(RedeclarationError(func_name, item.line, item.column))
                else:
                    # Add function to symbol table with a placeholder for parameters.
                    self.symbol_table.add(func_name, {"type": "function", "params": []})
            elif isinstance(item, list):
                # Assume this is the result from the 'param' transformer.
                params = item
        # Update the function info with the actual parameter list.
        if func_name:
            func_info = self.symbol_table.get(func_name)
            if func_info is not None:
                func_info["params"] = params

        # Enter a new scope for function parameters and body.
        self.symbol_table.enter_scope()
        for param in params:
            # Each parameter is stored as a tuple: (name, token)
            if isinstance(param, tuple):
                param_name, token = param
            else:
                param_name, token = param, None
            if token and self.symbol_table.is_declared_in_current_scope(param_name):
                self.errors.append(RedeclarationError(param_name, token.line, token.column))
            elif self.symbol_table.is_declared_in_current_scope(param_name):
                self.errors.append(RedeclarationError(param_name))
            else:
                self.symbol_table.add(param_name, {"type": "variable", "fixed": False, "assigned": True})
        # (Assume the function body has been processed by children.)
        self.symbol_table.exit_scope()
        return items

    # Process parameter list (rule: param)
    def param(self, items):
        # param: IDENTIFIER param_tail | empty
        # Return a list of tuples (param_name, token) so that we have location info.
        params = []
        for item in items:
            if isinstance(item, Token) and item.type == "IDENTIFIER":
                params.append((item.value, item))
        return params

    # Process function arguments (rule: args)
    def args(self, items):
        # args: expression args_tail | empty
        # Return a list of argument expressions (we only need the count for checking).
        args_list = []
        for item in items:
            # Filter out commas (if any appear as tokens)
            if not (isinstance(item, Token) and item.type == "COMMA"):
                args_list.append(item)
        return args_list

    # Process identifier usage (rule: id_usage)
    def id_usage(self, items):
        # id_usage: IDENTIFIER id_usagetail
        identifier_token = items[0]
        identifier = identifier_token.value
        # If there is a function call (id_usagetail being a func_call subtree), do function-check.
        if len(items) > 1 and isinstance(items[1], Tree) and items[1].data == "func_call":
            func_info = self.symbol_table.get(identifier)
            if func_info is None or func_info.get("type") != "function":
                self.errors.append(FunctionNotDefinedError(identifier, identifier_token.line, identifier_token.column))
            else:
                # Extract arguments from the func_call subtree.
                args_list = []
                for child in items[1].children:
                    if isinstance(child, Tree) and child.data == "args":
                        args_list = self.args(child.children)
                        break
                expected = len(func_info.get("params", []))
                got = len(args_list)
                if expected != got:
                    self.errors.append(ParameterMismatchError(identifier, expected, got, identifier_token.line, identifier_token.column))
        else:
            # Normal variable usage.
            if not self.symbol_table.exists(identifier):
                self.errors.append(UndefinedIdentifierError(identifier, identifier_token.line, identifier_token.column))
        return items

    # Pass-through methods for other rules.
    def declaration(self, items):
        return items

    def statement(self, items):
        return items

    def expression(self, items):
        return items

    def program(self, items):
        return items
