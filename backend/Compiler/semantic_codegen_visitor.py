from lark import Visitor, Token, Tree
from ..Semantic.symbol_table import SymbolTable, Symbol
from ..Semantic.semantic_errors import (
    SemanticError, UndefinedIdentifierError, RedeclarationError,
    FixedVarReassignmentError, TypeMismatchError, FunctionNotDefinedError,
    ParameterMismatchError, FunctionRedefinedError, ControlFlowError,
    InvalidListAccessError, InvalidGroupAccessError, ListIndexOutOfRangeError,
    InvalidListOperandError, TextIndexOutOfRangeError, KeyError
)
import re
class SemanticAndCodeGenVisitor(Visitor):
    def __init__(self):
        super().__init__()
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.scope_stack = [self.global_scope]
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.temp_types = {}
        self.errors = []
        self.current_function_symbol = None
        self.current_function_has_throw = False
        self.loop_stack = []
        self.TYPE_INT = 'integer'
        self.TYPE_POINT = 'point'
        self.TYPE_TEXT = 'text'
        self.TYPE_STATE = 'state'
        self.TYPE_LIST = 'list'
        self.TYPE_GROUP = 'group'
        self.TYPE_EMPTY = 'empty'
        self.TYPE_UNKNOWN = 'unknown'
        self.TYPE_FUNCTION = 'function'
        self.TYPE_PARAM = 'parameter'
        self.global_scope.define_function(name='show', params=['value'], is_builtin=True)
        self.global_scope.define_function(name='get', params=['prompt'], is_builtin=True) 
    def get_temp(self):
        """Generate a new temporary variable name."""
        self.temp_counter += 1
        temp_name = f"t{self.temp_counter}"
        self.temp_types[temp_name] = self.TYPE_UNKNOWN
        return temp_name
    def get_label(self):
        """Generate a new label for control flow."""
        self.label_counter += 1
        return f"L{self.label_counter}"
    def emit(self, op, arg1=None, arg2=None, result=None):
        """Emit a TAC instruction and infer temporary types."""
        clean_arg1 = self._clean_operand(arg1)
        clean_arg2 = self._clean_operand(arg2)
        clean_result = self._clean_operand(result)
        instruction = (op, clean_arg1, clean_arg2, clean_result)
        self.instructions.append(instruction)
        if isinstance(clean_result, str) and clean_result.startswith('t'):
            inferred_type = self.TYPE_UNKNOWN
            if op in ['ADD', 'SUB', 'MUL', 'MOD', 'NEG']:
                type1 = self._get_tac_operand_type(clean_arg1)
                type2 = self._get_tac_operand_type(clean_arg2)
                if type1 == self.TYPE_POINT or type2 == self.TYPE_POINT:
                    inferred_type = self.TYPE_POINT
                elif type1 == self.TYPE_STATE and type2 == self.TYPE_INT: inferred_type = self.TYPE_INT
                elif type1 == self.TYPE_INT and type2 == self.TYPE_STATE: inferred_type = self.TYPE_INT
                elif type1 == self.TYPE_STATE and type2 == self.TYPE_POINT: inferred_type = self.TYPE_POINT
                elif type1 == self.TYPE_POINT and type2 == self.TYPE_STATE: inferred_type = self.TYPE_POINT
                elif (type1 == self.TYPE_INT or type1 == self.TYPE_STATE) and \
                     (type2 == self.TYPE_INT or type2 == self.TYPE_STATE):
                     inferred_type = self.TYPE_INT
                elif op == 'NEG' and type1 in (self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE):
                    inferred_type = self.TYPE_POINT if type1 == self.TYPE_POINT else self.TYPE_INT
            elif op == 'DIV':
                inferred_type = self.TYPE_POINT
            elif op in ['LT', 'LE', 'GT', 'GE', 'EQ', 'NEQ', 'AND', 'OR', 'NOT']:
                inferred_type = self.TYPE_STATE
            elif op == 'CONCAT':
                inferred_type = self.TYPE_TEXT
            elif op == 'LIST_CONCAT':
                 inferred_type = self.TYPE_LIST
            elif op == 'LIST_ACCESS':
                 inferred_type = self.TYPE_UNKNOWN
            elif op == 'DICT_ACCESS':
                 inferred_type = self.TYPE_UNKNOWN
            elif op == 'TYPECAST':
                 inferred_type = clean_arg2 if isinstance(clean_arg2, str) and clean_arg2 in [self.TYPE_INT, self.TYPE_POINT, self.TYPE_TEXT, self.TYPE_STATE] else self.TYPE_UNKNOWN
            elif op == 'INPUT':
                 inferred_type = self.TYPE_TEXT 
            elif op == 'CALL':
                 inferred_type = self.TYPE_UNKNOWN
            elif op == 'ASSIGN':
                 inferred_type = self._get_tac_operand_type(clean_arg1)
            elif op == 'LIST_CREATE':
                 inferred_type = self.TYPE_LIST
            elif op == 'DICT_CREATE':
                 inferred_type = self.TYPE_GROUP
            self.temp_types[clean_result] = inferred_type
            return clean_result 
        return None 
    def _clean_operand(self, operand):
        """Helper to get the raw value for TAC, quoting strings."""
        if isinstance(operand, tuple) and len(operand) >= 1:
            op_type = operand[0]
            op_val = operand[1] if len(operand) > 1 else None
            if op_type == self.TYPE_TEXT:
                 if isinstance(op_val, str):
                      escaped_val = op_val.replace('\\', '\\\\').replace('"', '\\"')
                      return f'"{escaped_val}"'
                 return '""' 
            elif op_type == self.TYPE_STATE:
                 return str(op_val) 
            elif op_type == self.TYPE_EMPTY:
                 return 'None'
            return op_val
        elif isinstance(operand, Token):
            if operand.type == 'IDENTIFIER':
                return operand.value
            return operand.value 
        elif isinstance(operand, bool):
             return str(operand)
        elif operand is None:
             return 'None'
        return operand
    def _get_tac_operand_type(self, operand):
        """Infers the type of a TAC operand (temp, literal, var name)."""
        if isinstance(operand, str):
            if operand.startswith('t'): 
                return self.temp_types.get(operand, self.TYPE_UNKNOWN)
            elif operand.startswith('"') and operand.endswith('"'): 
                return self.TYPE_TEXT
            elif operand == 'None': 
                 return self.TYPE_EMPTY
            elif operand == 'True' or operand == 'False': 
                 return self.TYPE_STATE
            else: 
                symbol = self.current_scope.lookup_variable(operand)
                if symbol:
                    return symbol.var_type if symbol.var_type else self.TYPE_UNKNOWN
                try:
                    int(operand)
                    return self.TYPE_INT
                except ValueError:
                    try:
                        float(operand)
                        return self.TYPE_POINT
                    except ValueError:
                        return self.TYPE_UNKNOWN
        elif isinstance(operand, int): return self.TYPE_INT
        elif isinstance(operand, float): return self.TYPE_POINT
        elif isinstance(operand, bool): return self.TYPE_STATE
        elif operand is None: return self.TYPE_EMPTY
        return self.TYPE_UNKNOWN
    def push_scope(self):
        """Create a new scope and make it current."""
        new_scope = SymbolTable(parent=self.current_scope)
        self.current_scope = new_scope
        self.scope_stack.append(new_scope)
    def pop_scope(self):
        """Pop the current scope and revert to the parent."""
        if len(self.scope_stack) > 1:
            popped_scope = self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]
        else:
            pass 
    def add_error(self, error_class, message_args, node_or_token):
        """Adds a semantic error to the list, avoiding duplicates based on type, message, line, and column."""
        line = getattr(node_or_token, 'line', None)
        column = getattr(node_or_token, 'column', None)
        try:
            if isinstance(message_args, (list, tuple)):
                error = error_class(*message_args, line=line, column=column)
            else:
                error = error_class(message_args, line=line, column=column)
        except TypeError as e:
             print(f"Internal Error: Failed to create error {error_class.__name__} with args {message_args}. Error: {e}")
             error = SemanticError(str(message_args), line, column)
        except Exception as e:
             print(f"Internal Error: Unexpected error creating {error_class.__name__}: {e}")
             error = SemanticError(str(message_args), line, column)
        error_sig = (type(error), error.message, error.line, error.column)
        is_duplicate = any(
            type(e) == type(error) and e.message == error.message and e.line == error.line and e.column == error.column
            for e in self.errors
        )
        if not is_duplicate:
            self.errors.append(error)
    def get_operand_value_and_type(self, node):
        """
        Visits an operand/expression node, evaluates it, generates TAC,
        and returns its inferred type string and TAC result
        (literal value, variable name, or temporary variable name).
        Handles errors internally by calling add_error. Returns (None, None) on failure.
        """
        result = self.visit(node) 
        if result is None:
            if isinstance(node, Token) and node.type == 'EMPTY':
                return self.TYPE_EMPTY, None 
            return None, None
        if isinstance(result, tuple) and len(result) == 2:
            type_str, value = result
            if type_str == 'id': 
                symbol = self.current_scope.lookup_variable(value)
                if symbol:
                    return symbol.var_type if symbol.var_type else self.TYPE_UNKNOWN, value
                else:
                    if self.global_scope.lookup_function(value):
                         self.add_error(SemanticError, f"Cannot use function '{value}' as a value", node)
                    else:
                         self.add_error(UndefinedIdentifierError, value, node)
                    return None, None
            else: 
                return type_str, value
        elif isinstance(result, str):
            if result.startswith('t'): 
                temp_type = self.temp_types.get(result, self.TYPE_UNKNOWN)
                return temp_type, result 
            else: 
                symbol = self.current_scope.lookup_variable(result)
                if symbol:
                    return symbol.var_type if symbol.var_type else self.TYPE_UNKNOWN, result
                else:
                    if self.global_scope.lookup_function(result):
                         self.add_error(SemanticError, f"Cannot use function '{result}' as a value", node)
                    else:
                         self.add_error(UndefinedIdentifierError, result, node) 
                    return None, None
        elif isinstance(result, int): return self.TYPE_INT, result
        elif isinstance(result, float): return self.TYPE_POINT, result
        elif isinstance(result, bool): return self.TYPE_STATE, result
        elif isinstance(result, Token):
             self.add_error(SemanticError, f"Internal: Unexpected Token '{result.value}' received directly in get_operand_value_and_type", node)
             return None, None
        else:
            self.add_error(SemanticError, f"Internal: Unexpected result type '{type(result)}' from visit in get_operand_value_and_type", node)
            return None, None
    def analyze_and_generate(self, tree):
        """Main entry point to analyze and generate TAC."""
        self.visit(tree)
        unique_errors = []
        seen_errors = set()
        for error in self.errors:
             sig = (type(error), error.message, error.line, error.column)
             if sig not in seen_errors:
                 unique_errors.append(error)
                 seen_errors.add(sig)
        self.errors = unique_errors
        return self.errors, self.instructions
    def _is_get_call(self, node):
        """Checks if the AST node represents a 'get(...)' call."""
        if isinstance(node, Tree) and node.data == 'operand':
            if node.children and isinstance(node.children[0], Token) and node.children[0].type == 'GET':
                return True
        elif isinstance(node, Tree) and node.data == 'id_usage':
             if node.children and isinstance(node.children[0], Token) and node.children[0].value == 'get':
                  if len(node.children) > 1 and isinstance(node.children[1], Tree) and node.children[1].data == 'id_usagetail':
                       tail = node.children[1]
                       if tail.children and isinstance(tail.children[0], Tree) and tail.children[0].data == 'func_call':
                            return True
        return False
    def _get_prompt_from_get_call(self, node):
        """Extracts the prompt TAC result from a 'get' call node."""
        prompt_tac_result = '""' 
        prompt_node = None
        if isinstance(node, Tree) and node.data == 'operand' and node.children:
             if len(node.children) >= 4 and node.children[0].type == 'GET' and node.children[1].type == 'LPAREN':
                  prompt_node = node.children[2] 
        elif isinstance(node, Tree) and node.data == 'id_usage':
             try:
                  func_call_node = node.children[1].children[0]
                  if func_call_node.data == 'func_call' and len(func_call_node.children) > 1:
                       args_node = func_call_node.children[1]
                       if args_node.data == 'args' and args_node.children:
                            prompt_node = args_node.children[0] 
             except (IndexError, AttributeError):
                  pass 
        if prompt_node:
            prompt_type, tac_result = self.get_operand_value_and_type(prompt_node)
            if tac_result is not None:
                prompt_tac_result = tac_result
        return prompt_tac_result
    def visit_children_last(self, node, **kwargs): # Add **kwargs
        """Default visitor behavior: visit children and return the result of the last one."""
        last_result = None
        for child in node.children:
            if isinstance(child, (Tree, Token)):
                last_result = self.visit(child) # Don't pass kwargs here, visit handles it
        return last_result

    def visit(self, node, **kwargs): # Add **kwargs
        """Generic visit method for Tree and Token."""
        if isinstance(node, Token):
             # Tokens don't need extra context from parents usually
             return self.visit_token(node)
        elif isinstance(node, Tree):
            method_name = f"visit_{node.data}"
            visitor_method = getattr(self, method_name, None)
            if visitor_method:
                 # Check if the specific visitor method accepts kwargs
                 import inspect
                 sig = inspect.signature(visitor_method)
                 takes_kwargs = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())

                 if node.data in ['group_members', 'member_tail', 'list_value', 'list_tail',
                                  'func_recheck_statement', 'func_loop_recheck_statement',
                                  'program', 'program_block', 'start', 'expression',
                                  'primary_expr', 'literals', 'get_operand', 'id_usagetail', # Keep id_usagetail here for now, but it will be handled below
                                  'assign_op', 'loop_block', 'func_loop_block',
                                  'conditional_func_statement', 'loop_func_statement',
                                  'conditional_func_loop_statement', 'statements']:
                      # These generally just visit children, but check if the specific method exists and takes kwargs
                      if visitor_method and takes_kwargs:
                           return visitor_method(node, **kwargs) # Pass kwargs if accepted
                      elif visitor_method:
                           return visitor_method(node) # Call without kwargs if not accepted
                      else:
                           # Fallback to visit_children_last if no specific method
                           return self.visit_children_last(node, **kwargs) # Pass kwargs to visit_children_last
                 else:
                      # For other specific methods, pass kwargs if accepted
                      if takes_kwargs:
                           return visitor_method(node, **kwargs)
                      else:
                           # If the specific method doesn't take kwargs, but kwargs were passed,
                           # this might indicate an issue, but we'll call it without for now.
                           # Consider adding a warning here if needed.
                           return visitor_method(node)
            else:
                # No specific method found, use the default child visitor
                return self.visit_children_last(node, **kwargs) # Pass kwargs to visit_children_last
        else:
             return None
    def visit_token(self, token):
        """Visit a token node and return (type, value) or the Token itself for operators/keywords."""
        token_type = token.type
        value = token.value
        if token_type == 'TEXTLITERAL':
             processed_value = value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
             return (self.TYPE_TEXT, processed_value)
        elif token_type == 'INTEGERLITERAL':
            return (self.TYPE_INT, int(value))
        elif token_type == 'NEGINTEGERLITERAL':
            return (self.TYPE_INT, -int(value[1:]))
        elif token_type == 'POINTLITERAL':
            return (self.TYPE_POINT, float(value))
        elif token_type == 'NEGPOINTLITERAL':
            return (self.TYPE_POINT, -float(value[1:]))
        elif token_type == 'STATELITERAL':
            return (self.TYPE_STATE, value == "YES")
        elif token_type == 'EMPTY':
            return (self.TYPE_EMPTY, None)
        elif token_type == 'IDENTIFIER':
            return ('id', value)
        else:
             return token
    def visit_start(self, node): self.visit_children_last(node); return None
    def visit_program(self, node): self.visit_children_last(node); return None
    def visit_program_block(self, node): self.visit_children_last(node); return None
    def visit_varlist_declaration(self, node):
        identifier_token = node.children[1]
        var_name = identifier_token.value
        init_node = None
        tail_node = None
        current_index = 2
        if current_index < len(node.children) and isinstance(node.children[current_index], Tree) and node.children[current_index].data == 'var_init':
            init_node = node.children[current_index]
            current_index += 1
        if current_index < len(node.children) and isinstance(node.children[current_index], Tree) and node.children[current_index].data == 'varlist_tail':
            tail_node = node.children[current_index]
        if self.current_scope.lookup_variable(var_name, check_current_only=True):
            self.add_error(RedeclarationError, var_name, identifier_token)
            if tail_node:
                self.visit(tail_node)
            return None 
        symbol = self.current_scope.define_variable(
            name=var_name,
            fixed=False, 
            line=identifier_token.line,
            column=identifier_token.column,
            var_type=self.TYPE_EMPTY 
        )
        if not symbol:
            self.add_error(RedeclarationError, var_name, identifier_token)
            if tail_node: self.visit(tail_node)
            return None
        if init_node:
            if len(init_node.children) > 1:
                value_node = init_node.children[1] 
                if self._is_get_call(value_node):
                    prompt_tac_result = self._get_prompt_from_get_call(value_node)
                    input_temp = self.get_temp()
                    self.emit('INPUT', prompt_tac_result, None, input_temp)
                    self.emit('ASSIGN', input_temp, None, var_name)
                    symbol.var_type = self.TYPE_TEXT 
                else:
                    rhs_type, rhs_tac_result = self.get_operand_value_and_type(value_node)
                    if rhs_tac_result is not None:
                        self.emit('ASSIGN', rhs_tac_result, None, var_name)
                        symbol.var_type = rhs_type if rhs_type else self.TYPE_UNKNOWN
                    else:
                        symbol.var_type = self.TYPE_UNKNOWN
                        self.emit('ASSIGN', 'None', None, var_name) 
            else:
                self.add_error(SemanticError, "Malformed variable initialization", init_node)
                symbol.var_type = self.TYPE_EMPTY
                self.emit('ASSIGN', 'None', None, var_name) 
        else:
            symbol.var_type = self.TYPE_EMPTY
            self.emit('ASSIGN', 'None', None, var_name) 
        if tail_node:
            self.visit(tail_node) 
        return None 
    def visit_varlist_tail(self, node):
        if not node.children or len(node.children) < 2:
            return None 
        identifier_token = node.children[1]
        var_name = identifier_token.value
        init_node = None
        tail_node = None
        current_index = 2
        if current_index < len(node.children) and isinstance(node.children[current_index], Tree) and node.children[current_index].data == 'var_init':
            init_node = node.children[current_index]
            current_index += 1
        if current_index < len(node.children) and isinstance(node.children[current_index], Tree) and node.children[current_index].data == 'varlist_tail':
            tail_node = node.children[current_index]
        if self.current_scope.lookup_variable(var_name, check_current_only=True):
            self.add_error(RedeclarationError, var_name, identifier_token)
            if tail_node: self.visit(tail_node)
            return None
        symbol = self.current_scope.define_variable(
            name=var_name,
            fixed=False,
            line=identifier_token.line,
            column=identifier_token.column,
            var_type=self.TYPE_EMPTY
        )
        if not symbol:
            self.add_error(RedeclarationError, var_name, identifier_token)
            if tail_node: self.visit(tail_node)
            return None
        if init_node:
            if len(init_node.children) > 1:
                value_node = init_node.children[1]
                if self._is_get_call(value_node):
                    prompt_tac_result = self._get_prompt_from_get_call(value_node)
                    input_temp = self.get_temp()
                    self.emit('INPUT', prompt_tac_result, None, input_temp)
                    self.emit('ASSIGN', input_temp, None, var_name)
                    symbol.var_type = self.TYPE_TEXT
                else:
                    rhs_type, rhs_tac_result = self.get_operand_value_and_type(value_node)
                    if rhs_tac_result is not None:
                        self.emit('ASSIGN', rhs_tac_result, None, var_name)
                        symbol.var_type = rhs_type if rhs_type else self.TYPE_UNKNOWN
                    else:
                        symbol.var_type = self.TYPE_UNKNOWN
                        self.emit('ASSIGN', 'None', None, var_name)
            else:
                self.add_error(SemanticError, "Malformed variable initialization", init_node)
                symbol.var_type = self.TYPE_EMPTY
                self.emit('ASSIGN', 'None', None, var_name)
        else:
            symbol.var_type = self.TYPE_EMPTY
            self.emit('ASSIGN', 'None', None, var_name)
        if tail_node:
            self.visit(tail_node)
        return None
    def visit_fixed_declaration(self, node):
        identifier_token = node.children[1]
        var_name = identifier_token.value
        value_node = node.children[3] 
        tail_node = None
        current_index = 4
        if current_index < len(node.children) and isinstance(node.children[current_index], Tree) and node.children[current_index].data == 'fixed_tail':
            tail_node = node.children[current_index]
        if self.current_scope.lookup_variable(var_name, check_current_only=True):
            self.add_error(RedeclarationError, var_name, identifier_token)
            if tail_node: self.visit(tail_node)
            return None
        symbol = self.current_scope.define_variable(
            name=var_name,
            fixed=True, 
            line=identifier_token.line,
            column=identifier_token.column,
            var_type=self.TYPE_EMPTY 
        )
        if not symbol:
            self.add_error(RedeclarationError, var_name, identifier_token)
            if tail_node: self.visit(tail_node)
            return None
        if self._is_get_call(value_node):
            prompt_tac_result = self._get_prompt_from_get_call(value_node)
            input_temp = self.get_temp()
            self.emit('INPUT', prompt_tac_result, None, input_temp)
            self.emit('ASSIGN', input_temp, None, var_name)
            symbol.var_type = self.TYPE_TEXT 
        else:
            rhs_type, rhs_tac_result = self.get_operand_value_and_type(value_node)
            if rhs_tac_result is not None:
                self.emit('ASSIGN', rhs_tac_result, None, var_name)
                symbol.var_type = rhs_type if rhs_type else self.TYPE_UNKNOWN
            else:
                symbol.var_type = self.TYPE_UNKNOWN
                self.emit('ASSIGN', 'None', None, var_name) 
        if tail_node:
            self.visit(tail_node)
        return None
    def visit_fixed_tail(self, node):
        if not node.children or len(node.children) < 4:
            return None 
        identifier_token = node.children[1]
        var_name = identifier_token.value
        value_node = node.children[3] 
        tail_node = None
        if len(node.children) > 4 and isinstance(node.children[4], Tree) and node.children[4].data == 'fixed_tail':
            tail_node = node.children[4]
        if self.current_scope.lookup_variable(var_name, check_current_only=True):
            self.add_error(RedeclarationError, var_name, identifier_token)
            if tail_node: self.visit(tail_node)
            return None
        symbol = self.current_scope.define_variable(
            name=var_name,
            fixed=True,
            line=identifier_token.line,
            column=identifier_token.column,
            var_type=self.TYPE_EMPTY
        )
        if not symbol:
            self.add_error(RedeclarationError, var_name, identifier_token)
            if tail_node: self.visit(tail_node)
            return None
        if self._is_get_call(value_node):
            prompt_tac_result = self._get_prompt_from_get_call(value_node)
            input_temp = self.get_temp()
            self.emit('INPUT', prompt_tac_result, None, input_temp)
            self.emit('ASSIGN', input_temp, None, var_name)
            symbol.var_type = self.TYPE_TEXT
        else:
            rhs_type, rhs_tac_result = self.get_operand_value_and_type(value_node)
            if rhs_tac_result is not None:
                self.emit('ASSIGN', rhs_tac_result, None, var_name)
                symbol.var_type = rhs_type if rhs_type else self.TYPE_UNKNOWN
            else:
                symbol.var_type = self.TYPE_UNKNOWN
                self.emit('ASSIGN', 'None', None, var_name)
        if tail_node:
            self.visit(tail_node)
        return None
    def visit_group_declaration(self, node):
        identifier_token = node.children[1]
        group_name = identifier_token.value
        members_node = node.children[4] 
        if self.current_scope.lookup_variable(group_name, check_current_only=True):
            self.add_error(RedeclarationError, group_name, identifier_token)
            return None
        if self.global_scope.lookup_function(group_name):
            self.add_error(RedeclarationError, f"Identifier '{group_name}' already defined as a function", identifier_token)
            return None
        symbol = self.current_scope.define_variable(
            name=group_name,
            fixed=False, 
            line=identifier_token.line,
            column=identifier_token.column,
            var_type=self.TYPE_GROUP
        )
        if not symbol:
            self.add_error(RedeclarationError, group_name, identifier_token) 
            return None
        group_temp = self.get_temp()
        self.emit('DICT_CREATE', None, None, group_temp) 
        literal_keys_seen = {} 
        if members_node.data == 'group_members':
            self.visit(members_node, group_temp=group_temp, literal_keys_seen=literal_keys_seen) 
        self.emit('ASSIGN', group_temp, None, group_name)
        return None
    def visit_group_members(self, node, group_temp, literal_keys_seen): # Keep parameters
        if not node or not node.children or len(node.children) < 3:
            return
        key_node = node.children[0]
        value_node = node.children[2]
        tail_node = node.children[3] if len(node.children) > 3 and isinstance(node.children[3], Tree) and node.children[3].data == 'member_tail' else None
        key_type, key_tac_result = self.get_operand_value_and_type(key_node)
        value_type, value_tac_result = self.get_operand_value_and_type(value_node)
        valid_key_types = [self.TYPE_INT, self.TYPE_POINT, self.TYPE_TEXT, self.TYPE_STATE]
        is_valid_key = False
        if key_type in valid_key_types:
            is_valid_key = True
        elif key_type == self.TYPE_UNKNOWN:
             if isinstance(key_tac_result, str) and not key_tac_result.startswith('t') and not key_tac_result.startswith('"'):
                  is_valid_key = True 
             else:
                  pass 
        if not is_valid_key:
            self.add_error(TypeMismatchError,
                           f"Group key must be integer, point, text, or state, not {key_type or 'invalid expression'}",
                           key_node)
        elif key_tac_result is not None: 
            key_is_literal = not (isinstance(key_tac_result, str) and (key_tac_result.startswith('t') or self.current_scope.lookup_variable(key_tac_result)))
            key_is_literal_refined = isinstance(key_tac_result, (int, float, bool)) or \
                                     (isinstance(key_tac_result, str) and key_tac_result.startswith('"')) or \
                                     key_tac_result == 'None' or key_tac_result == 'True' or key_tac_result == 'False'
            if key_is_literal_refined:
                key_literal_val_cleaned = self._clean_operand((key_type, key_tac_result))
                key_sig = (key_type, key_literal_val_cleaned)
                if key_sig in literal_keys_seen:
                    self.add_error(KeyError, f"Duplicate key {key_literal_val_cleaned} in group literal", key_node)
                else:
                    literal_keys_seen[key_sig] = True
                    if value_tac_result is not None: 
                        self.emit('DICT_SET', group_temp, key_tac_result, value_tac_result)
            else: 
                if value_tac_result is not None: 
                    self.emit('DICT_SET', group_temp, key_tac_result, value_tac_result)
        if tail_node:
            self.visit(tail_node, group_temp=group_temp, literal_keys_seen=literal_keys_seen)
    def visit_member_tail(self, node, group_temp, literal_keys_seen): # Keep parameters
        if node.children and len(node.children) > 1 and isinstance(node.children[1], Tree) and node.children[1].data == 'group_members':
            self.visit(node.children[1], group_temp=group_temp, literal_keys_seen=literal_keys_seen)
    def visit_variable_value(self, node):
        if not node.children:
             return (self.TYPE_EMPTY, None) 
        first_child = node.children[0]
        if isinstance(first_child, Token) and first_child.type == 'LSQB':
            list_temp = self.get_temp()
            self.emit('LIST_CREATE', None, None, list_temp) 
            list_value_node = None
            if len(node.children) > 2 and isinstance(node.children[1], Tree) and node.children[1].data == 'list_value':
                list_value_node = node.children[1]
            if list_value_node:
                self.visit(list_value_node, list_temp=list_temp)
            return (self.TYPE_LIST, list_temp)
        elif isinstance(first_child, Token) and first_child.type == 'LBRACE':
             group_temp = self.get_temp()
             self.emit('DICT_CREATE', None, None, group_temp)
             members_node = None
             if len(node.children) > 2 and isinstance(node.children[1], Tree) and node.children[1].data == 'group_members':
                  members_node = node.children[1]
             if members_node:
                  literal_keys_seen = {}
                  self.visit(members_node, group_temp=group_temp, literal_keys_seen=literal_keys_seen) 
             return (self.TYPE_GROUP, group_temp)
        elif isinstance(first_child, Token) and first_child.type == 'GET':
             if len(node.children) >= 4: 
                  prompt_node = node.children[2]
                  prompt_tac_result = self._get_prompt_from_get_call(node) 
                  input_temp = self.get_temp()
                  self.emit('INPUT', prompt_tac_result, None, input_temp)
                  return input_temp 
             else:
                  self.add_error(SemanticError, "Malformed GET operation in variable value", node)
                  return (self.TYPE_UNKNOWN, None) 
        elif isinstance(first_child, Tree): 
            return self.visit(first_child)
        elif isinstance(first_child, Token): 
             return self.visit(first_child)
        else:
            self.add_error(SemanticError, "Unexpected structure in variable_value", node)
            return (self.TYPE_UNKNOWN, None)
    def visit_list_value(self, node, list_temp): # Keep parameter
        if not node.children: return None
        item_node = node.children[0] 
        tail_node = None
        if len(node.children) > 1 and isinstance(node.children[1], Tree) and node.children[1].data == 'list_tail':
            tail_node = node.children[1]
        item_type, item_tac_result = self.get_operand_value_and_type(item_node)
        if item_tac_result is not None:
            self.emit('LIST_APPEND', list_temp, item_tac_result) 
        if tail_node:
            self.visit(tail_node, list_temp=list_temp) 
    def visit_list_tail(self, node, list_temp): # Keep parameter
        if not node.children or len(node.children) < 2: return None
        item_node = node.children[1] 
        tail_node = None
        if len(node.children) > 2 and isinstance(node.children[2], Tree) and node.children[2].data == 'list_tail':
            tail_node = node.children[2]
        item_type, item_tac_result = self.get_operand_value_and_type(item_node)
        if item_tac_result is not None:
            self.emit('LIST_APPEND', list_temp, item_tac_result)
        if tail_node:
            self.visit(tail_node, list_temp=list_temp) 
    def visit_expression(self, node):
        if node.children:
            return self.visit(node.children[0])
        self.add_error(SemanticError, "Empty expression node", node)
        return None 
    def visit_logical_or_expr(self, node):
        if len(node.children) == 1:
            return self.visit(node.children[0])
        left_operand_node = node.children[0]
        left_type, left_tac_result = self.get_operand_value_and_type(left_operand_node)
        if left_tac_result is None:
             return None 
        if left_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
             self.add_error(TypeMismatchError, f"Operator 'OR' requires state type, not {left_type}", left_operand_node)
        result_temp = self.get_temp()
        self.emit('ASSIGN', left_tac_result, None, result_temp) 
        end_label = self.get_label() 
        i = 1
        while i < len(node.children):
            right_operand_node = node.children[i+1]
            next_check_label = self.get_label()
            self.emit('IFFALSE', result_temp, None, next_check_label) 
            self.emit('GOTO', None, None, end_label) 
            self.emit('LABEL', None, None, next_check_label) 
            right_type, right_tac_result = self.get_operand_value_and_type(right_operand_node)
            if right_tac_result is None:
                return None 
            if right_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
                 self.add_error(TypeMismatchError, f"Operator 'OR' requires state type, not {right_type}", right_operand_node)
            self.emit('ASSIGN', right_tac_result, None, result_temp)
            i += 2 
        self.emit('LABEL', None, None, end_label) 
        self.temp_types[result_temp] = self.TYPE_STATE 
        return result_temp 
    def visit_logical_and_expr(self, node):
        if len(node.children) == 1:
            return self.visit(node.children[0])
        left_operand_node = node.children[0]
        left_type, left_tac_result = self.get_operand_value_and_type(left_operand_node)
        if left_tac_result is None:
            return None
        if left_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
             self.add_error(TypeMismatchError, f"Operator 'AND' requires state type, not {left_type}", left_operand_node)
        result_temp = self.get_temp()
        self.emit('ASSIGN', left_tac_result, None, result_temp)
        end_label = self.get_label() 
        i = 1
        while i < len(node.children):
            right_operand_node = node.children[i+1]
            next_check_label = self.get_label()
            self.emit('IFTRUE', result_temp, None, next_check_label) 
            self.emit('GOTO', None, None, end_label) 
            self.emit('LABEL', None, None, next_check_label) 
            right_type, right_tac_result = self.get_operand_value_and_type(right_operand_node)
            if right_tac_result is None:
                return None
            if right_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
                 self.add_error(TypeMismatchError, f"Operator 'AND' requires state type, not {right_type}", right_operand_node)
            self.emit('ASSIGN', right_tac_result, None, result_temp)
            i += 2
        self.emit('LABEL', None, None, end_label)
        self.temp_types[result_temp] = self.TYPE_STATE 
        return result_temp
    def visit_equality_expr(self, node):
        if len(node.children) == 1:
            return self.visit(node.children[0])
        if len(node.children) != 3:
             self.add_error(SemanticError, "Malformed equality expression", node)
             return None
        left_operand_node = node.children[0]
        op_token = node.children[1] 
        right_operand_node = node.children[2]
        left_type, left_tac_result = self.get_operand_value_and_type(left_operand_node)
        right_type, right_tac_result = self.get_operand_value_and_type(right_operand_node)
        if left_tac_result is None or right_tac_result is None:
             return None 
        op_map = {'==': 'EQ', '!=': 'NEQ'}
        tac_op = op_map.get(op_token.value)
        if tac_op:
             temp_result = self.get_temp()
             self.emit(tac_op, left_tac_result, right_tac_result, temp_result)
             self.temp_types[temp_result] = self.TYPE_STATE 
             return temp_result
        else:
             self.add_error(SemanticError, f"Unsupported equality operator '{op_token.value}'", op_token)
             return None
    def visit_relational_expr(self, node):
        if len(node.children) == 1:
            return self.visit(node.children[0])
        if len(node.children) != 3:
             self.add_error(SemanticError, "Malformed relational expression", node)
             return None
        left_operand_node = node.children[0]
        op_token = node.children[1] 
        right_operand_node = node.children[2]
        left_type, left_tac_result = self.get_operand_value_and_type(left_operand_node)
        right_type, right_tac_result = self.get_operand_value_and_type(right_operand_node)
        if left_tac_result is None or right_tac_result is None:
            return None
        allowed_types = [self.TYPE_INT, self.TYPE_POINT, self.TYPE_TEXT, self.TYPE_STATE, self.TYPE_UNKNOWN]
        numeric_types = [self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE] 
        is_numeric_compare = left_type in numeric_types and right_type in numeric_types
        is_text_compare = left_type == self.TYPE_TEXT and right_type == self.TYPE_TEXT
        is_unknown_involved = left_type == self.TYPE_UNKNOWN or right_type == self.TYPE_UNKNOWN
        if not (is_numeric_compare or is_text_compare or is_unknown_involved):
             self.add_error(TypeMismatchError,
                            f"Cannot compare types {left_type} and {right_type} with '{op_token.value}'",
                            op_token)
        op_map = {'<': 'LT', '<=': 'LE', '>': 'GT', '>=': 'GE'}
        tac_op = op_map.get(op_token.value)
        if tac_op:
            temp_result = self.get_temp()
            self.emit(tac_op, left_tac_result, right_tac_result, temp_result)
            self.temp_types[temp_result] = self.TYPE_STATE 
            return temp_result
        else:
            self.add_error(SemanticError, f"Unsupported relational operator '{op_token.value}'", op_token)
            return None
    def visit_add_expr(self, node):
        if len(node.children) == 1:
            return self.visit(node.children[0])
        left_operand_node = node.children[0]
        current_type, current_tac_result = self.get_operand_value_and_type(left_operand_node)
        if current_tac_result is None: return None
        i = 1
        while i < len(node.children):
            op_token = node.children[i] 
            right_operand_node = node.children[i+1]
            right_type, right_tac_result = self.get_operand_value_and_type(right_operand_node)
            if right_tac_result is None: return None
            op = op_token.value
            temp_result = self.get_temp() 
            if op == '+':
                 if current_type == self.TYPE_TEXT or right_type == self.TYPE_TEXT:
                      self.emit('CONCAT', current_tac_result, right_tac_result, temp_result)
                      current_type = self.TYPE_TEXT 
                 elif current_type == self.TYPE_LIST and right_type == self.TYPE_LIST:
                      self.emit('LIST_CONCAT', current_tac_result, right_tac_result, temp_result)
                      current_type = self.TYPE_LIST 
                 elif current_type == self.TYPE_LIST or right_type == self.TYPE_LIST:
                      self.add_error(TypeMismatchError, f"Cannot add type '{right_type if current_type == self.TYPE_LIST else current_type}' to list using '+'", op_token)
                      return None 
                 elif current_type in (self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN) and \
                      right_type in (self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN):
                      self.emit('ADD', current_tac_result, right_tac_result, temp_result)
                      if current_type == self.TYPE_POINT or right_type == self.TYPE_POINT:
                           current_type = self.TYPE_POINT
                      elif current_type == self.TYPE_UNKNOWN or right_type == self.TYPE_UNKNOWN:
                           current_type = self.TYPE_UNKNOWN 
                      else:
                           current_type = self.TYPE_INT
                 else:
                      self.add_error(TypeMismatchError, f"Cannot add types {current_type} and {right_type} using '+'", op_token)
                      return None 
            elif op == '-':
                 if current_type in (self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN) and \
                    right_type in (self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN):
                     self.emit('SUB', current_tac_result, right_tac_result, temp_result)
                     if current_type == self.TYPE_POINT or right_type == self.TYPE_POINT:
                          current_type = self.TYPE_POINT
                     elif current_type == self.TYPE_UNKNOWN or right_type == self.TYPE_UNKNOWN:
                          current_type = self.TYPE_UNKNOWN
                     else:
                          current_type = self.TYPE_INT
                 else:
                     self.add_error(TypeMismatchError, f"Cannot subtract types {current_type} and {right_type}", op_token)
                     return None 
            current_tac_result = temp_result
            i += 2 
        return current_tac_result
    def visit_mul_expr(self, node):
        if len(node.children) == 1:
            return self.visit(node.children[0])
        left_operand_node = node.children[0]
        current_type, current_tac_result = self.get_operand_value_and_type(left_operand_node)
        if current_tac_result is None: return None
        i = 1
        while i < len(node.children):
            op_token = node.children[i] 
            right_operand_node = node.children[i+1]
            right_type, right_tac_result = self.get_operand_value_and_type(right_operand_node)
            if right_tac_result is None: return None
            op = op_token.value
            temp_result = self.get_temp()
            numeric_types = [self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN]
            if current_type not in numeric_types or right_type not in numeric_types:
                 self.add_error(TypeMismatchError, f"Operator '{op}' requires numeric/state types, not {current_type} and {right_type}", op_token)
                 return None 
            op_map = {'*': 'MUL', '/': 'DIV', '%': 'MOD'}
            tac_op = op_map.get(op)
            if tac_op:
                 self.emit(tac_op, current_tac_result, right_tac_result, temp_result)
                 if tac_op == 'DIV':
                      current_type = self.TYPE_POINT 
                 elif current_type == self.TYPE_POINT or right_type == self.TYPE_POINT:
                      current_type = self.TYPE_POINT 
                 elif current_type == self.TYPE_UNKNOWN or right_type == self.TYPE_UNKNOWN:
                      current_type = self.TYPE_UNKNOWN 
                 else:
                      current_type = self.TYPE_INT 
            else:
                 self.add_error(SemanticError, f"Unsupported multiplicative operator '{op}'", op_token)
                 return None
            current_tac_result = temp_result
            i += 2
        return current_tac_result
    def visit_pre_expr(self, node):
        if len(node.children) == 1:
            return self.visit(node.children[0])
        elif len(node.children) == 2:
            op_token = node.children[0] 
            operand_node = node.children[1] 
            operand_type, operand_tac_result = self.get_operand_value_and_type(operand_node)
            if operand_tac_result is None: return None
            temp_result = self.get_temp()
            if op_token.type == 'NOT': 
                 if operand_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
                      self.add_error(TypeMismatchError, f"Operator '!' requires state type, not {operand_type}", op_token)
                 self.emit('NOT', operand_tac_result, None, temp_result)
                 self.temp_types[temp_result] = self.TYPE_STATE 
                 return temp_result
            elif op_token.type == 'NEG': 
                 numeric_types = [self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN]
                 if operand_type not in numeric_types:
                      self.add_error(TypeMismatchError, f"Operator '~' requires numeric/state type, not {operand_type}", op_token)
                      return None 
                 self.emit('NEG', operand_tac_result, None, temp_result)
                 self.temp_types[temp_result] = self.TYPE_POINT if operand_type == self.TYPE_POINT else self.TYPE_INT
                 if operand_type == self.TYPE_UNKNOWN: self.temp_types[temp_result] = self.TYPE_UNKNOWN
                 return temp_result
            else:
                self.add_error(SemanticError, f"Unsupported prefix operator '{op_token.value}'", op_token)
                return None
        else:
             self.add_error(SemanticError, "Malformed prefix expression", node)
             return None
    def visit_primary_expr(self, node):
        if len(node.children) == 3 and isinstance(node.children[0], Token) and node.children[0].type == 'LPAREN':
             return self.visit(node.children[1])
        elif len(node.children) == 1:
             return self.visit(node.children[0])
        else:
            self.add_error(SemanticError, "Malformed primary expression node", node)
            return None
    def visit_operand(self, node):
        child = node.children[0] if node.children else None
        if not child:
             self.add_error(SemanticError, "Empty operand node", node)
             return None
        if isinstance(child, Token) and child.type == 'GET':
            if len(node.children) >= 4:
                 prompt_tac_result = self._get_prompt_from_get_call(node) 
                 temp = self.get_temp()
                 self.emit('INPUT', prompt_tac_result, None, temp)
                 self.temp_types[temp] = self.TYPE_TEXT 
                 return temp 
            else:
                 self.add_error(SemanticError, "Malformed GET operation in operand", node)
                 return None
        else:
            return self.visit(child)
    def visit_literals(self, node):
        if node.children:
            return self.visit(node.children[0])
        self.add_error(SemanticError, "Empty literals node", node)
        return None
    def visit_typecast_expression(self, node):
        target_type_token = node.children[0] 
        expr_node = node.children[2]
        target_type_str = self.TYPE_UNKNOWN
        token_val = target_type_token.value.lower() 
        if token_val == 'to_integer': target_type_str = self.TYPE_INT
        elif token_val == 'to_point': target_type_str = self.TYPE_POINT
        elif token_val == 'to_text': target_type_str = self.TYPE_TEXT
        elif token_val == 'to_state': target_type_str = self.TYPE_STATE
        else:
             self.add_error(SemanticError, f"Unknown typecast target '{target_type_token.value}'", target_type_token)
             return None
        source_type, source_tac_result = self.get_operand_value_and_type(expr_node)
        if source_tac_result is None: return None 
        temp_result = self.get_temp()
        self.emit('TYPECAST', source_tac_result, target_type_str, temp_result)
        self.temp_types[temp_result] = target_type_str 
        return temp_result
    def visit_get_operand(self, node):
         if node.children:
             return self.visit(node.children[0])
         return (self.TYPE_TEXT, "") 
    def visit_id_usage(self, node):
        identifier_token = node.children[0]
        var_name = identifier_token.value
        tail_node = node.children[1] if len(node.children) > 1 else None
        base_symbol = self.current_scope.lookup_variable(var_name)
        is_function = False
        if not base_symbol:
            func_symbol = self.global_scope.lookup_function(var_name)
            if func_symbol:
                is_function = True
                base_symbol = func_symbol 
            else:
                self.add_error(UndefinedIdentifierError, var_name, identifier_token)
                return None 
        if tail_node:
            if isinstance(tail_node, Tree) and tail_node.data == 'id_usagetail':
                 return self.visit_id_usagetail(tail_node, base_var_name=var_name, base_symbol=base_symbol)
            else:
                 return self.visit(tail_node) 
        else:
            if is_function:
                self.add_error(SemanticError, f"Cannot use function '{var_name}' as a value without calling it", identifier_token)
                return None
            else:
                return ('id', var_name)
    def visit_id_usagetail(self, node, base_var_name, base_symbol): # Keep parameters here
        access_node = None
        unary_op_node = None
        func_call_node = None
        if node.children[0].data == 'func_call':
            func_call_node = node.children[0]
        elif node.children[0].data == 'group_or_list':
            access_node = node.children[0]
            if len(node.children) > 1 and node.children[1].data == 'unary_op':
                unary_op_node = node.children[1]
        else:
             self.add_error(SemanticError, "Internal: Unexpected structure in id_usagetail", node)
             return None
        if func_call_node:
            if base_symbol.kind != 'function':
                 self.add_error(SemanticError, f"Identifier '{base_var_name}' is not a function, cannot call it", node)
                 return None
            if base_symbol.is_builtin:
                 args_node = func_call_node.children[1] if len(func_call_node.children) > 1 else None
                 arg_tac_results = self.visit(args_node) if args_node else [] 
                 if base_var_name == 'show':
                      if len(arg_tac_results) != 1:
                           self.add_error(ParameterMismatchError, (base_var_name, 1, len(arg_tac_results)), node)
                           return None
                      self.emit('PRINT', arg_tac_results[0])
                      return None 
                 elif base_var_name == 'get':
                      prompt_tac = '""'
                      if len(arg_tac_results) == 1:
                           prompt_tac = arg_tac_results[0]
                      elif len(arg_tac_results) > 1:
                           self.add_error(ParameterMismatchError, (base_var_name, 1, len(arg_tac_results)), node)
                      input_temp = self.get_temp()
                      self.emit('INPUT', prompt_tac, None, input_temp)
                      self.temp_types[input_temp] = self.TYPE_TEXT
                      return input_temp 
                 else:
                      self.add_error(SemanticError, f"Built-in function '{base_var_name}' not fully handled yet", node)
                      return None
            else: 
                args_node = func_call_node.children[1] if len(func_call_node.children) > 1 and func_call_node.children[1].data == 'args' else None
                arg_tac_results = self.visit(args_node) if args_node else []
                expected_params = len(base_symbol.params)
                provided_args = len(arg_tac_results)
                if expected_params != provided_args:
                    self.add_error(ParameterMismatchError, (base_var_name, expected_params, provided_args), node)
                    return None
                for i, arg_result in enumerate(arg_tac_results):
                    self.emit('PARAM', arg_result, None, i)
                return_temp = self.get_temp()
                self.temp_types[return_temp] = self.TYPE_UNKNOWN
                self.emit('CALL', base_var_name, provided_args, return_temp)
                return return_temp
        elif access_node:
            if base_symbol.kind != 'variable':
                 self.add_error(SemanticError, f"Cannot apply element access to non-variable '{base_var_name}'", node)
                 return None
            if not access_node.children:
                 self.add_error(SemanticError, "Internal: Empty group_or_list node found in tail", access_node)
                 return None
            accessor_token = access_node.children[0]
            index_node = access_node.children[1]
            is_list_access = accessor_token.type == 'LSQB'
            is_group_access = accessor_token.type == 'LBRACE'
            base_type = base_symbol.var_type
            index_type, index_tac_result = self.get_operand_value_and_type(index_node)
            if index_tac_result is None: return None
            temp_result = self.get_temp()
            if is_list_access:
                if base_type not in [self.TYPE_LIST, self.TYPE_TEXT, self.TYPE_UNKNOWN]:
                    self.add_error(InvalidListAccessError, f"Cannot apply index '[]' to type {base_type}", accessor_token)
                    return None
                if index_type not in [self.TYPE_INT, self.TYPE_UNKNOWN]:
                    self.add_error(TypeMismatchError, f"List/Text index must be an integer, not {index_type}", index_node)
                self.emit('LIST_ACCESS', base_var_name, index_tac_result, temp_result)
                self.temp_types[temp_result] = self.TYPE_UNKNOWN 
            elif is_group_access:
                if base_type not in [self.TYPE_GROUP, self.TYPE_UNKNOWN]:
                    self.add_error(InvalidGroupAccessError, f"Cannot apply key access '{{}}' to type {base_type}", accessor_token)
                    return None
                valid_key_types = [self.TYPE_INT, self.TYPE_POINT, self.TYPE_TEXT, self.TYPE_STATE, self.TYPE_UNKNOWN]
                if index_type not in valid_key_types:
                    self.add_error(TypeMismatchError, f"Group key must be integer, point, text, or state, not {index_type}", index_node)
                self.emit('DICT_ACCESS', base_var_name, index_tac_result, temp_result)
                self.temp_types[temp_result] = self.TYPE_UNKNOWN 
            else:
                self.add_error(SemanticError, "Invalid access operation", access_node)
                return None
            if unary_op_node:
                if not unary_op_node.children: 
                     return temp_result 
                op_token = unary_op_node.children[0] 
                if base_symbol.fixed:
                     self.add_error(FixedVarReassignmentError, f"Cannot modify element of fixed {base_type} '{base_var_name}'", op_token)
                     return None
                original_value_temp = self.get_temp()
                self.emit('ASSIGN', temp_result, None, original_value_temp) 
                self.temp_types[original_value_temp] = self.temp_types.get(temp_result, self.TYPE_UNKNOWN) 
                op_tac = 'ADD' if op_token.type == 'INC_OP' else 'SUB'
                modify_temp = self.get_temp()
                self.emit(op_tac, temp_result, 1, modify_temp) 
                set_op = 'LIST_SET' if is_list_access else 'DICT_SET'
                self.emit(set_op, base_var_name, index_tac_result, modify_temp)
                return original_value_temp 
            else:
                return temp_result
        else:
             self.add_error(SemanticError, "Internal: Unhandled id_usagetail structure", node)
             return None
    def visit_func_call(self, node):
        if len(node.children) > 1 and isinstance(node.children[1], Tree) and node.children[1].data == 'args':
            return self.visit(node.children[1]) 
        return [] 
    def visit_args(self, node):
        arg_tac_results = []
        for child in node.children:
            if isinstance(child, Tree): 
                arg_type, arg_tac_result = self.get_operand_value_and_type(child)
                if arg_tac_result is not None:
                    arg_tac_results.append(arg_tac_result)
                else:
                     arg_tac_results.append(None) 
            elif isinstance(child, Token) and child.type == 'COMMA':
                continue
            else:
                 self.add_error(SemanticError, f"Unexpected item '{child}' in argument list", child)
        return arg_tac_results
    def visit_group_or_list(self, node):
        if len(node.children) > 1:
            index_node = node.children[1]
            idx_type, idx_tac_result = self.get_operand_value_and_type(index_node)
            return idx_tac_result
        self.add_error(SemanticError, "Malformed group or list accessor", node)
        return None
    def visit_unary_op(self, node):
        return node.children[0] if node.children else None
    def visit_statements(self, node):
        for child in node.children:
             if isinstance(child, Tree): 
                 self.visit(child)
        return None 
    def visit_var_assign(self, node):
        identifier_token = node.children[0]
        target_var_name = identifier_token.value
        target_symbol = self.current_scope.lookup_variable(target_var_name)
        if not target_symbol:
            self.add_error(UndefinedIdentifierError, target_var_name, identifier_token)
            return None
        accessor_node = None
        assign_op_node = None
        value_node = None
        cursor = 1
        if cursor < len(node.children) and isinstance(node.children[cursor], Tree) and node.children[cursor].data == 'group_or_list':
            accessor_node = node.children[cursor]
            cursor += 1
        if cursor < len(node.children):
            if isinstance(node.children[cursor], Tree) and node.children[cursor].data == 'assign_op':
                 assign_op_node = node.children[cursor] 
            elif isinstance(node.children[cursor], Token) and node.children[cursor].type in ['ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'STAR_ASSIGN', 'SLASH_ASSIGN', 'MOD_ASSIGN']: 
                 assign_op_node = node.children[cursor] 
            else:
                 self.add_error(SemanticError, f"Expected assignment operator, found {node.children[cursor]}", node.children[cursor] if cursor < len(node.children) else identifier_token)
                 return None
            cursor += 1
        else:
             self.add_error(SemanticError, "Missing assignment operator", identifier_token)
             return None
        if cursor < len(node.children) and isinstance(node.children[cursor], Tree) and node.children[cursor].data == 'variable_value':
            value_node = node.children[cursor]
        else:
             self.add_error(SemanticError, "Missing value in assignment", assign_op_node or identifier_token)
             return None
        op_token = self.visit(assign_op_node) if isinstance(assign_op_node, Tree) else assign_op_node
        if op_token is None or not hasattr(op_token, 'value'):
             self.add_error(SemanticError, "Invalid assignment operator structure", assign_op_node)
             return None
        op = op_token.value 
        rhs_type, rhs_tac_result = self.get_operand_value_and_type(value_node)
        if rhs_tac_result is None:
             return None
        if accessor_node:
            if target_symbol.fixed:
                 self.add_error(FixedVarReassignmentError, f"Cannot modify element of fixed {target_symbol.var_type} '{target_var_name}'", identifier_token)
                 return None
            base_type = target_symbol.var_type
            accessor_type_token = accessor_node.children[0] 
            index_node = accessor_node.children[1]
            is_list_access = accessor_type_token.type == 'LSQB'
            is_group_access = accessor_type_token.type == 'LBRACE'
            index_type, index_tac_result = self.get_operand_value_and_type(index_node)
            if index_tac_result is None: return None 
            expected_index_type = None
            if is_list_access:
                 if base_type not in [self.TYPE_LIST, self.TYPE_TEXT, self.TYPE_UNKNOWN]:
                      self.add_error(InvalidListAccessError, f"Cannot apply index '[]' assignment to type {base_type}", accessor_type_token)
                      return None
                 expected_index_type = self.TYPE_INT
                 if index_type not in [expected_index_type, self.TYPE_UNKNOWN]:
                      self.add_error(TypeMismatchError, f"List/Text index must be an integer, not {index_type}", index_node)
            elif is_group_access:
                 if base_type not in [self.TYPE_GROUP, self.TYPE_UNKNOWN]:
                      self.add_error(InvalidGroupAccessError, f"Cannot apply key access '{{}}' assignment to type {base_type}", accessor_type_token)
                      return None
                 expected_index_type = [self.TYPE_INT, self.TYPE_POINT, self.TYPE_TEXT, self.TYPE_STATE] 
                 if index_type not in expected_index_type + [self.TYPE_UNKNOWN]:
                      self.add_error(TypeMismatchError, f"Group key must be integer, point, text, or state, not {index_type}", index_node)
            tac_op_set = 'LIST_SET' if is_list_access else 'DICT_SET'
            tac_op_access = 'LIST_ACCESS' if is_list_access else 'DICT_ACCESS'
            if op == '=':
                 self.emit(tac_op_set, target_var_name, index_tac_result, rhs_tac_result)
            else: 
                 current_val_temp = self.get_temp()
                 self.emit(tac_op_access, target_var_name, index_tac_result, current_val_temp)
                 current_type = self.TYPE_UNKNOWN
                 result_temp = self.get_temp()
                 compound_op_map = {'+=': 'ADD', '-=': 'SUB', '*=': 'MUL', '/=': 'DIV', '%=': 'MOD'} 
                 arith_op = compound_op_map.get(op)
                 if arith_op:
                     if op == '+=':
                          if rhs_type == self.TYPE_TEXT:
                               self.emit('CONCAT', current_val_temp, rhs_tac_result, result_temp)
                          elif rhs_type == self.TYPE_LIST and base_type == self.TYPE_LIST: 
                               self.emit('LIST_CONCAT', current_val_temp, rhs_tac_result, result_temp)
                          else: 
                               self.emit('ADD', current_val_temp, rhs_tac_result, result_temp)
                     else:
                          self.emit(arith_op, current_val_temp, rhs_tac_result, result_temp)
                     self.emit(tac_op_set, target_var_name, index_tac_result, result_temp)
                 else:
                      self.add_error(SemanticError, f"Unsupported compound assignment operator '{op}' for element assignment", op_token)
                      return None
        else:
            if target_symbol.fixed:
                 self.add_error(FixedVarReassignmentError, target_var_name, identifier_token)
                 return None
            if op == '=':
                target_symbol.var_type = rhs_type if rhs_type else self.TYPE_UNKNOWN
                self.emit('ASSIGN', rhs_tac_result, None, target_var_name)
            else: 
                current_type = target_symbol.var_type
                result_temp = self.get_temp() 
                compound_op_map = {'+=': 'ADD', '-=': 'SUB', '*=': 'MUL', '/=': 'DIV', '%=': 'MOD'}
                tac_op = compound_op_map.get(op)
                if tac_op:
                     new_type = self.TYPE_UNKNOWN 
                     if op == '+=':
                          if current_type == self.TYPE_TEXT or rhs_type == self.TYPE_TEXT:
                               self.emit('CONCAT', target_var_name, rhs_tac_result, result_temp)
                               new_type = self.TYPE_TEXT
                          elif current_type == self.TYPE_LIST and rhs_type == self.TYPE_LIST:
                               self.emit('LIST_CONCAT', target_var_name, rhs_tac_result, result_temp)
                               new_type = self.TYPE_LIST
                          elif current_type == self.TYPE_LIST or rhs_type == self.TYPE_LIST:
                               self.add_error(TypeMismatchError, f"Cannot add type '{rhs_type if current_type == self.TYPE_LIST else current_type}' to list using '+='", op_token)
                               return None
                          elif current_type in (self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN) and \
                               rhs_type in (self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN):
                               self.emit('ADD', target_var_name, rhs_tac_result, result_temp)
                               if current_type == self.TYPE_POINT or rhs_type == self.TYPE_POINT: new_type = self.TYPE_POINT
                               elif current_type == self.TYPE_UNKNOWN or rhs_type == self.TYPE_UNKNOWN: new_type = self.TYPE_UNKNOWN
                               else: new_type = self.TYPE_INT
                          else:
                               self.add_error(TypeMismatchError, f"Cannot apply operator '{op}' to types {current_type} and {rhs_type}", op_token)
                               return None
                     elif current_type in (self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN) and \
                          rhs_type in (self.TYPE_INT, self.TYPE_POINT, self.TYPE_STATE, self.TYPE_UNKNOWN):
                          self.emit(tac_op, target_var_name, rhs_tac_result, result_temp)
                          if tac_op == 'DIV': new_type = self.TYPE_POINT
                          elif current_type == self.TYPE_POINT or rhs_type == self.TYPE_POINT: new_type = self.TYPE_POINT
                          elif current_type == self.TYPE_UNKNOWN or rhs_type == self.TYPE_UNKNOWN: new_type = self.TYPE_UNKNOWN
                          else: new_type = self.TYPE_INT
                     else: 
                          self.add_error(TypeMismatchError, f"Cannot apply operator '{op}' to types {current_type} and {rhs_type}", op_token)
                          return None
                     self.emit('ASSIGN', result_temp, None, target_var_name)
                     target_symbol.var_type = new_type
                else:
                     self.add_error(SemanticError, f"Unsupported compound assignment operator '{op}'", op_token)
                     return None
        return None 
    def visit_assign_op(self, node):
        return node.children[0] if node.children else None
    def visit_checkif_statement(self, node):
        condition_node = node.children[2]
        true_block_node = node.children[5] 
        recheck_or_otherwise_node = None
        if len(node.children) > 7 and isinstance(node.children[6], Tree):
             node_data = node.children[6].data
             if node_data in ['recheck_statement', 'func_recheck_statement', 'func_loop_recheck_statement',
                              'otherwise_statement', 'func_otherwise_statement', 'func_loop_otherwise_statement']:
                  recheck_or_otherwise_node = node.children[6]
        cond_type, cond_tac_result = self.get_operand_value_and_type(condition_node)
        if cond_tac_result is None:
            return None
        if cond_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
             self.add_error(TypeMismatchError, f"CHECKIF condition must be state type, not {cond_type}", condition_node)
        false_label = self.get_label() 
        end_label = self.get_label()   
        self.emit('IFFALSE', cond_tac_result, None, false_label)
        self.push_scope() 
        self.visit(true_block_node)
        self.pop_scope()
        self.emit('GOTO', None, None, end_label)
        self.emit('LABEL', None, None, false_label) 
        if recheck_or_otherwise_node:
            node_data = recheck_or_otherwise_node.data
            if node_data in ['recheck_statement', 'func_recheck_statement', 'func_loop_recheck_statement']:
                 self.visit_recheck_statement(recheck_or_otherwise_node, end_label) 
            elif node_data in ['otherwise_statement', 'func_otherwise_statement', 'func_loop_otherwise_statement']:
                 self.visit(recheck_or_otherwise_node) 
        self.emit('LABEL', None, None, end_label)
        return None
    def visit_recheck_statement(self, node, checkif_end_label): # Accept end label
        condition_node = node.children[2]
        true_block_node = node.children[5]
        next_recheck_or_otherwise = None
        if len(node.children) > 7 and isinstance(node.children[6], Tree):
             node_data = node.children[6].data
             if node_data in ['recheck_statement', 'func_recheck_statement', 'func_loop_recheck_statement',
                              'otherwise_statement', 'func_otherwise_statement', 'func_loop_otherwise_statement']:
                  next_recheck_or_otherwise = node.children[6]
        cond_type, cond_tac_result = self.get_operand_value_and_type(condition_node)
        if cond_tac_result is None: return None
        if cond_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
             self.add_error(TypeMismatchError, f"RECHECK condition must be state type, not {cond_type}", condition_node)
        false_label = self.get_label() 
        self.emit('IFFALSE', cond_tac_result, None, false_label)
        self.push_scope()
        self.visit(true_block_node)
        self.pop_scope()
        self.emit('GOTO', None, None, checkif_end_label)
        self.emit('LABEL', None, None, false_label)
        if next_recheck_or_otherwise:
            node_data = next_recheck_or_otherwise.data
            if node_data in ['recheck_statement', 'func_recheck_statement', 'func_loop_recheck_statement']:
                 self.visit_recheck_statement(next_recheck_or_otherwise, checkif_end_label)
            elif node_data in ['otherwise_statement', 'func_otherwise_statement', 'func_loop_otherwise_statement']:
                 self.visit(next_recheck_or_otherwise)
        return None
    def visit_otherwise_statement(self, node):
        otherwise_block_node = node.children[1] 
        self.push_scope()
        self.visit(otherwise_block_node)
        self.pop_scope()
        return None
    def visit_switch_statement(self, node):
        switch_expr_node = node.children[2]
        switch_expr_type, switch_expr_tac_result = self.get_operand_value_and_type(switch_expr_node)
        if switch_expr_tac_result is None:
            return None 
        end_switch_label = self.get_label() 
        default_target_label = None 
        next_case_test_label = self.get_label() 
        case_blocks_info = [] 
        default_block_node = None
        current_node_index = 5
        while current_node_index < len(node.children):
            child_node = node.children[current_node_index]
            if not isinstance(child_node, Tree):
                 current_node_index += 1 
                 continue
            node_data = child_node.data
            if node_data in ['case_tail', 'func_case_tail', 'func_loop_case_tail']:
                if len(child_node.children) >= 4:
                    case_value_node = child_node.children[1] 
                    case_block_node = child_node.children[3] 
                    case_value_type, case_value_tac = self.get_operand_value_and_type(case_value_node)
                    if case_value_tac is not None:
                        case_code_label = self.get_label() 
                        case_blocks_info.append((case_value_tac, case_value_node, case_block_node, case_code_label))
                else:
                     self.add_error(SemanticError, f"Malformed case statement: {node_data}", child_node)
            elif node_data in ['default', 'func_switch_default', 'func_loop_switch_default']:
                 if default_target_label is not None:
                      self.add_error(SemanticError, "Multiple default blocks in switch statement", child_node)
                 elif len(child_node.children) >= 3:
                      default_block_node = child_node.children[2]
                      default_target_label = self.get_label() 
                 else:
                      self.add_error(SemanticError, f"Malformed default statement: {node_data}", child_node)
            current_node_index += 1
        for i, (case_val_tac, case_val_node, _, case_code_label) in enumerate(case_blocks_info):
            self.emit('LABEL', None, None, next_case_test_label) 
            temp_eq = self.get_temp()
            self.emit('EQ', switch_expr_tac_result, case_val_tac, temp_eq)
            self.temp_types[temp_eq] = self.TYPE_STATE
            self.emit('IFTRUE', temp_eq, None, case_code_label)
            if i < len(case_blocks_info) - 1:
                 next_case_test_label = self.get_label() 
                 self.emit('GOTO', None, None, next_case_test_label) 
            else:
                 fallthrough_label = default_target_label if default_target_label else end_switch_label
                 self.emit('GOTO', None, None, fallthrough_label)
        self.emit('LABEL', None, None, next_case_test_label) 
        if default_target_label:
            self.emit('GOTO', None, None, default_target_label)
        else:
            self.emit('GOTO', None, None, end_switch_label)
        for case_val_tac, case_val_node, case_block_node, case_code_label in case_blocks_info:
            self.emit('LABEL', None, None, case_code_label) 
            self.push_scope() 
            self.visit(case_block_node)
            self.pop_scope()
            self.emit('GOTO', None, None, end_switch_label)
        if default_target_label and default_block_node:
            self.emit('LABEL', None, None, default_target_label) 
            self.push_scope() 
            self.visit(default_block_node)
            self.pop_scope()
            self.emit('GOTO', None, None, end_switch_label) 
        self.emit('LABEL', None, None, end_switch_label)
        return None
    def visit_case_tail(self, node):
         pass
         return None
    def visit_default(self, node):
         pass
         return None
    def visit_each_statement(self, node):
        init_node = node.children[2]
        condition_node = node.children[4]
        update_node = node.children[6]
        body_node = node.children[9] 
        cond_label = self.get_label()    
        body_label = self.get_label()    
        update_label = self.get_label()  
        end_label = self.get_label()     
        self.loop_stack.append((update_label, end_label))
        self.push_scope() 
        self.visit(init_node) 
        self.emit('GOTO', None, None, cond_label) 
        self.emit('LABEL', None, None, body_label)
        self.visit(body_node)
        self.emit('LABEL', None, None, update_label)
        self.visit(update_node) 
        self.emit('LABEL', None, None, cond_label)
        cond_type, cond_tac_result = self.get_operand_value_and_type(condition_node)
        if cond_tac_result is None:
             self.emit('GOTO', None, None, end_label)
        else:
             if cond_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
                  self.add_error(TypeMismatchError, f"EACH loop condition must be state type, not {cond_type}", condition_node)
             self.emit('IFTRUE', cond_tac_result, None, body_label)
        self.emit('LABEL', None, None, end_label)
        self.pop_scope() 
        self.loop_stack.pop() 
        return None
    def visit_repeat_statement(self, node):
        condition_node = node.children[3]
        body_node = node.children[6] 
        start_label = self.get_label() 
        body_label = self.get_label()  
        end_label = self.get_label()   
        self.loop_stack.append((start_label, end_label))
        self.emit('LABEL', None, None, start_label)
        cond_type, cond_tac_result = self.get_operand_value_and_type(condition_node)
        if cond_tac_result is None:
             self.emit('GOTO', None, None, end_label) 
        else:
             if cond_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
                  self.add_error(TypeMismatchError, f"REPEAT WHILE condition must be state type, not {cond_type}", condition_node)
             self.emit('IFFALSE', cond_tac_result, None, end_label)
        self.emit('LABEL', None, None, body_label) 
        self.push_scope() 
        self.visit(body_node)
        self.pop_scope()
        self.emit('GOTO', None, None, start_label)
        self.emit('LABEL', None, None, end_label)
        self.loop_stack.pop()
        return None
    def visit_do_repeat_statement(self, node):
        body_node = node.children[1] 
        condition_node = node.children[5]
        start_label = self.get_label() 
        cond_label = self.get_label()  
        end_label = self.get_label()   
        self.loop_stack.append((cond_label, end_label))
        self.emit('LABEL', None, None, start_label)
        self.push_scope() 
        self.visit(body_node)
        self.pop_scope()
        self.emit('LABEL', None, None, cond_label)
        cond_type, cond_tac_result = self.get_operand_value_and_type(condition_node)
        if cond_tac_result is None:
             self.emit('GOTO', None, None, end_label) 
        else:
            if cond_type not in [self.TYPE_STATE, self.TYPE_UNKNOWN]:
                 self.add_error(TypeMismatchError, f"DO REPEAT condition must be state type, not {cond_type}", condition_node)
            self.emit('IFTRUE', cond_tac_result, None, start_label)
        self.emit('LABEL', None, None, end_label)
        self.loop_stack.pop()
        return None
    def visit_loop_block(self, node):
        for child in node.children:
             if isinstance(child, Tree):
                 self.visit(child)
        return None
    def visit_control_flow(self, node):
        control_token = node.children[0]
        control_type = control_token.value.lower() 
        if not self.loop_stack:
            self.add_error(ControlFlowError, (f"'{control_type}'", "loop"), control_token)
            return None
        update_or_cond_label, end_label = self.loop_stack[-1]
        if control_type == 'exit':
            self.emit('GOTO', None, None, end_label)
        elif control_type == 'next':
            self.emit('GOTO', None, None, update_or_cond_label)
        else:
             self.add_error(SemanticError, f"Unknown control flow statement '{control_type}'", control_token)
        return None
    def visit_func_definition(self, node):
        func_token = node.children[1]
        func_name = func_token.value
        param_node = node.children[3] 
        body_node = node.children[5]  
        if self.global_scope.lookup_function(func_name):
            self.add_error(FunctionRedefinedError, func_name, func_token)
            return None 
        if self.global_scope.lookup_variable(func_name):
            self.add_error(RedeclarationError,
                           f"Identifier '{func_name}' already defined as a variable",
                           func_token)
            return None
        param_names = self.visit(param_node) 
        if param_names is None:
            return None 
        func_symbol = self.global_scope.define_function(
            name=func_name,
            params=param_names, 
            line=func_token.line,
            column=func_token.column,
            is_builtin=False
        )
        if not func_symbol:
            self.add_error(FunctionRedefinedError, func_name, func_token)
            return None
        func_entry_label = f"FUNC_{func_name}" 
        func_end_label = self.get_label() 
        self.emit('GOTO', None, None, func_end_label)
        self.emit('LABEL', None, None, func_entry_label)
        self.emit('FUNCTION_BEGIN', func_name, len(param_names), func_entry_label) 
        self.current_function_symbol = func_symbol
        self.current_function_has_throw = False 
        self.push_scope() 
        for i, pname in enumerate(param_names):
            param_symbol = self.current_scope.define_variable(
                name=pname,
                fixed=False, 
                var_type=self.TYPE_UNKNOWN, 
                is_param=True,
                param_index=i 
            )
            if not param_symbol:
                self.add_error(SemanticError, f"Internal error defining parameter '{pname}'", func_token)
        self.visit(body_node)
        self.pop_scope() 
        last_op_info = self.instructions[-1] if self.instructions else None
        needs_implicit_return = True
        if self.current_function_has_throw: 
             needs_implicit_return = False
        elif last_op_info and last_op_info[0] in ['RETURN', 'GOTO']: 
             needs_implicit_return = False
        implicit_return_label = f"IMPLICIT_RETURN_{func_name}"
        self.emit('LABEL', None, None, implicit_return_label)
        if needs_implicit_return:
            self.emit('RETURN', 'None', None, None) 
        self.emit('FUNCTION_END', func_name, None, None) 
        self.emit('LABEL', None, None, func_end_label)
        self.current_function_symbol = None
        return None 
    def visit_param(self, node):
        param_names = []
        seen_params = set()
        if not node.children: 
            return param_names
        first_child = node.children[0]
        if isinstance(first_child, Token) and first_child.type == 'EMPTY':
            return param_names
        for child in node.children:
            if isinstance(child, Token) and child.type == 'IDENTIFIER':
                param_name = child.value
                if param_name in seen_params:
                    self.add_error(RedeclarationError,
                                   f"Duplicate parameter name '{param_name}'",
                                   child)
                    param_names = None 
                elif param_names is not None: 
                    param_names.append(param_name)
                    seen_params.add(param_name)
            elif isinstance(child, Token) and child.type == 'COMMA':
                continue 
            else:
                self.add_error(SemanticError, f"Unexpected token '{child}' in parameter list", child)
                param_names = None 
        return param_names 
    def visit_throw_statement(self, node):
        if not self.current_function_symbol:
            self.add_error(ControlFlowError, "'throw' statement outside of function", node.children[0]) 
            return None
        expr_node = node.children[1]
        ret_type, ret_tac_result = self.get_operand_value_and_type(expr_node)
        if ret_tac_result is not None:
            self.emit('RETURN', ret_tac_result, None, None)
            self.current_function_has_throw = True
        return None 
    def visit_var_init(self, node):
        if len(node.children) > 1:
            return self.visit(node.children[1]) 
        self.add_error(SemanticError, "Malformed variable initialization", node)
        return None
    def visit_conditional_func_statement(self, node): 
        if node.children: self.visit(node.children[0]); return None
    def visit_func_checkif_statement(self, node): 
        return self.visit_checkif_statement(node)
    def visit_func_recheck_statement(self, node, end_label): # Add end_label parameter
        return self.visit_recheck_statement(node, end_label) # Delegate and pass label
    def visit_func_otherwise_statement(self, node): 
        return self.visit_otherwise_statement(node)
    def visit_func_switch_statement(self, node): 
        return self.visit_switch_statement(node)
    def visit_func_case_tail(self, node): 
        return self.visit_case_tail(node)
    def visit_func_switch_default(self, node): 
        return self.visit_default(node)
    def visit_loop_func_statement(self, node): 
        if node.children: self.visit(node.children[0]); return None
    def visit_each_func_statement(self, node): 
        return self.visit_each_statement(node)
    def visit_repeat_func_statement(self, node): 
        return self.visit_repeat_statement(node)
    def visit_do_repeat_func_statement(self, node): 
        return self.visit_do_repeat_statement(node)
    def visit_func_loop_block(self, node): 
        return self.visit_loop_block(node)
    def visit_conditional_func_loop_statement(self, node): 
        if node.children: self.visit(node.children[0]); return None
    def visit_func_loop_checkif_statement(self, node): 
        return self.visit_checkif_statement(node)
    def visit_func_loop_recheck_statement(self, node, end_label): # Add end_label parameter
        return self.visit_recheck_statement(node, end_label) # Delegate and pass label
    def visit_func_loop_otherwise_statement(self, node): 
        return self.visit_otherwise_statement(node)
    def visit_func_loop_switch_statement(self, node): 
        return self.visit_switch_statement(node)
    def visit_func_loop_case_tail(self, node): 
        return self.visit_case_tail(node)
    def visit_func_loop_switch_default(self, node): 
        return self.visit_default(node)
    def visit_block(self, node):
        if len(node.children) == 3 and node.children[0].type == 'LBRACE':
             statements_node = node.children[1]
             if isinstance(statements_node, Tree) and statements_node.data == 'statements':
                  self.visit(statements_node)
        elif len(node.children) == 2 and node.children[0].type == 'LBRACE':
             pass 
        elif len(node.children) == 1 and isinstance(node.children[0], Tree): 
             allowed_single_statements = ['var_assign', 'checkif_statement', 'switch_statement', 'each_statement', 'repeat_statement', 'do_repeat_statement', 'throw_statement', 'id_usage'] 
             if node.children[0].data in allowed_single_statements:
                 self.visit(node.children[0]) 
             else:
                 self.add_error(SemanticError, f"Unexpected single item '{node.children[0].data}' used as block", node)
        else:
             for child in node.children:
                  if isinstance(child, Tree):
                       self.visit(child)
        return None 
    def visit_statement(self, node):
        if node.children:
            actual_statement_node = node.children[0]
            return self.visit(actual_statement_node)
        self.add_error(SemanticError, "Empty statement node", node)
        return None
    def visit_declaration(self, node):
        if node.children:
            actual_declaration_node = node.children[0]
            return self.visit(actual_declaration_node)
        self.add_error(SemanticError, "Empty declaration node", node)
        return None
    def visit_conditional_statement(self, node):
        if node.children:
            actual_conditional_node = node.children[0]
            return self.visit(actual_conditional_node)
        self.add_error(SemanticError, "Empty conditional statement node", node)
        return None
    def visit_loop_statement(self, node):
        if node.children:
            actual_loop_node = node.children[0]
            return self.visit(actual_loop_node)
        self.add_error(SemanticError, "Empty loop statement node", node)
        return None
    def visit_init_expr(self, node):
        if node.children:
            return self.visit(node.children[0])
        return None 
    def visit_cond_expr(self, node):
        if node.children:
            return self.visit(node.children[0])
        return (self.TYPE_STATE, True) 
    def visit_update_expr(self, node):
        if node.children:
            return self.visit(node.children[0])
        return None 
    def visit_key_expr(self, node):
        if node.children:
            return self.visit(node.children[0])
        self.add_error(SemanticError, "Empty key expression in group", node)
        return None
    def visit_value_expr(self, node):
        if node.children:
            return self.visit(node.children[0])
        self.add_error(SemanticError, "Empty value expression in group", node)
        return None
