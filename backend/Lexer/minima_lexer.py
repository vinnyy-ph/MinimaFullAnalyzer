from .tokens import Token as T
from .errors import (
    InvalidIdentifierError,
    LexerError,
    InvalidIntegerError,
    InvalidPointError,
    InvalidSymbolError,
    LexerWarning
)
from .states import LexerState
from .delims import *
from .constants import ATOMS

class Lexer:
    def __init__(self, input_code):
        # Normalize newlines
        self.code = input_code.replace('\r\n', '\n').replace('\r', '\n')
        self.position = 0
        self.line = 1
        self.column = 1

        # This is the FSM's current state
        self.current_state = LexerState.INITIAL

        # Buffers and outputs
        self.errors = []           # Collect errors here
        self.token_buffer = []

        # Map each distinct identifier name to a unique label
        self.identifier_map = {}
        
        # Increment this each time we encounter a *new* identifier
        self.identifier_count = 0

        # Symbol sets and delimiter definitions
        self.symbols = [
            '+', '-', '*', '/', '%', '=', '!', '>', '<', '&', '|',
            '{', '}', '(', ')', '[', ']', ':', ',', ';'
        ]

        self.current_char = self.code[self.position] if self.code else None

    #--------------------------------------------------------------------------
    # Low-level helpers
    #--------------------------------------------------------------------------

    def advance(self):
        """
        Move to the next character, updating line and column numbers.
        """
        
        if self.current_char == '\n':
            self.line += 1
            self.column = 0
            
        #increment position and column ONLY (no moving of tracked characters)
        self.position += 1
        self.column += 1
        
        # Update current_char to the next character in the code
        if self.position < len(self.code):
            self.current_char = self.code[self.position]
        else:
            self.current_char = None

    def peek_next_char(self, offset=1):
        """
        Look ahead in the code without consuming characters.
        """
        next_pos = self.position + offset 
        if next_pos < len(self.code):
            return self.code[next_pos]
        return None
    
    def get_identifier_label(self, identifier_name):
        """
        Returns 'IDENTIFIER_1', 'IDENTIFIER_2', etc. for a given
        identifier name, reusing existing labels if we've seen it before.
        """
        if identifier_name not in self.identifier_map:
            self.identifier_count += 1
            self.identifier_map[identifier_name] = f"IDENTIFIER_{self.identifier_count}"
        return self.identifier_map[identifier_name]

    #--------------------------------------------------------------------------
    # Keyword checking
    #--------------------------------------------------------------------------
    def keyword_check(self, value: str):
        
        # ----- Starts with 'a' -----
        if value[0] == 'a':
            # Could be "abs"
            if len(value) == 3 and value[1] == 'b' and value[2] == 's':
                return 'abs'

        # ----- Check if it starts with 'c' -----
        if value[0] == 'c':
            if len(value) == 4 and value[1] == 'a' and value[2] == 's' and value[3] == 'e':
                return 'case'
            elif len(value) == 7 and value[1] == 'h' and value[2] == 'e' and value[3] == 'c' and value[4] == 'k' and value[5] == 'i' and value[6] == 'f':
                return 'checkif'
            elif len(value) == 8 and value[1] == 'o' and value[2] == 'n' and value[3] == 't' and value[4] == 'a' and value[5] == 'i' and value[6] == 'n' and value[7] == 's':
                return 'contains'
            elif len(value) == 4 and value[1] == 'e' and value[2] == 'i' and value[3] == 'l':
                return 'ceil'

        # ----- Starts with 'd' -----
        if value[0] == 'd':
            # Could be "default" or "do"
            if len(value) == 7 and value[1] == 'e' and value[2] == 'f' and value[3] == 'a' and value[4] == 'u' and value[5] == 'l' and value[6] == 't':
                return 'default'
            elif len(value) == 2 and value[1] == 'o':
                return 'do'

        # ----- Starts with 'e' -----
        if value[0] == 'e':
            # Could be "each", "empty", or "exit"
            if len(value) == 4 and value[1] == 'a' and value[2] == 'c' and value[3] == 'h':
                return 'each'
            elif len(value) == 5 and value[1] == 'm' and value[2] == 'p' and value[3] == 't' and value[4] == 'y':
                return 'empty'
            elif len(value) == 4 and value[1] == 'x' and value[2] == 'i' and value[3] == 't':
                return 'exit'

        # ----- Starts with 'f' -----
        if value[0] == 'f':
            # Could be "fixed", "func", "factorial", "floor"
            if len(value) == 5 and value[1] == 'i' and value[2] == 'x' and value[3] == 'e' and value[4] == 'd':
                return 'fixed'
            elif len(value) == 4 and value[1] == 'u' and value[2] == 'n' and value[3] == 'c':
                return 'func'
            elif len(value) == 9 and value[1] == 'a' and value[2] == 'c' and value[3] == 't' and value[4] == 'o' and value[5] == 'r' and value[6] == 'i' and value[7] == 'a' and value[8] == 'l':
                return 'factorial'
            elif len(value) == 5 and value[1] == 'l' and value[2] == 'o' and value[3] == 'o' and value[4] == 'r':
                return 'floor'

        # ----- Starts with 'g' -----
        if value[0] == 'g':
            # Could be "get", "group"
            if len(value) == 3 and value[1] == 'e' and value[2] == 't':
                return 'get'
            elif len(value) == 5 and value[1] == 'r' and value[2] == 'o' and value[3] == 'u' and value[4] == 'p':
                return 'group'

        # ----- Starts with 'i' -----
        if value[0] == 'i':
            # Could be "integer", "indexOf", "isqrt"
            if len(value) == 7 and value[1] == 'n' and value[2] == 't' and value[3] == 'e' and value[4] == 'g' and value[5] == 'e' and value[6] == 'r':
                return 'integer'
            elif len(value) == 5 and value[1] == 's' and value[2] == 'q' and value[3] == 'r' and value[4] == 't':
                return 'isqrt'

        # ----- Starts with 'j' -----
        if value[0] == 'j':
            if len(value) == 4 and value[1] == 'o' and value[2] == 'i' and value[3] == 'n':
                return 'join'

        # ----- Starts with 'l' -----
        if value[0] == 'l':
            if len(value) == 6 and value[1] == 'e' and value[2] == 'n' and value[3] == 'g' and value[4] == 't' and value[5] == 'h':
                return 'length'
            elif len(value) == 9 and value[1] == 'o' and value[2] == 'w' and value[3] == 'e' and value[4] == 'r' and value[5] == 'c' and value[6] == 'a' and value[7] == 's' and value[8] == 'e':
                return 'lowercase'

        # ----- Starts with 'm' -----
        if value[0] == 'm':
            if len(value) == 3 and value[1] == 'a' and value[2] == 'x':
                return 'max'
            elif len(value) == 3 and value[1] == 'i' and value[2] == 'n':
                return 'min'
            elif len(value) == 5 and value[1] == 'a' and value[2] == 't' and value[3] == 'c' and value[4] == 'h':
                return 'match'

        # ----- Starts with 'n' -----
        if value[0] == 'n':
            # Could be "next"
            if len(value) == 4 and value[1] == 'e' and value[2] == 'x' and value[3] == 't':
                return 'next'

        # ----- Starts with 'o' -----
        if value[0] == 'o':
            # Could be "otherwise"
            if len(value) == 9 and value[1] == 't' and value[2] == 'h' and value[3] == 'e' and value[4] == 'r' and value[5] == 'w' and value[6] == 'i' and value[7] == 's' and value[8] == 'e':
                return 'otherwise'

        # ----- Starts with 'p' -----
        if value[0] == 'p':
            # Could be "point", "pow"
            if len(value) == 5 and value[1] == 'o' and value[2] == 'i' and value[3] == 'n' and value[4] == 't':
                return 'point'
            elif len(value) == 3 and value[1] == 'o' and value[2] == 'w':
                return 'pow'

        # ----- Starts with 'r' -----
        if value[0] == 'r':
            # Could be "recheck", "repeat", "reverse", "round"
            if len(value) == 7 and value[1] == 'e' and value[2] == 'c' and value[3] == 'h' and value[4] == 'e' and value[5] == 'c' and value[6] == 'k':
                return 'recheck'
            elif len(value) == 6 and value[1] == 'e' and value[2] == 'p' and value[3] == 'e' and value[4] == 'a' and value[5] == 't':
                return 'repeat'
            elif len(value) == 7 and value[1] == 'e' and value[2] == 'v' and value[3] == 'e' and value[4] == 'r' and value[5] == 's' and value[6] == 'e':
                return 'reverse'
            elif len(value) == 5 and value[1] == 'o' and value[2] == 'u' and value[3] == 'n' and value[4] == 'd':
                return 'round'

        # ----- Starts with 's' -----
        if value[0] == 's':
            # Could be "show", "state", "sorted", "sum", "slice"
            if len(value) == 4 and value[1] == 'h' and value[2] == 'o' and value[3] == 'w':
                return 'show'
            elif len(value) == 5 and value[1] == 't' and value[2] == 'a' and value[3] == 't' and value[4] == 'e':
                return 'state'
            elif len(value) == 6 and value[1] == 'o' and value[2] == 'r' and value[3] == 't' and value[4] == 'e' and value[5] == 'd':
                return 'sorted'
            elif len(value) == 3 and value[1] == 'u' and value[2] == 'm':
                return 'sum'
            elif len(value) == 5 and value[1] == 'l' and value[2] == 'i' and value[3] == 'c' and value[4] == 'e':
                return 'slice'

        # ----- Starts with 't' -----
        if value[0] == 't':
            # Could be "text", "throw", "type"
            if len(value) == 4 and value[1] == 'e' and value[2] == 'x' and value[3] == 't':
                return 'text'
            elif len(value) == 5 and value[1] == 'h' and value[2] == 'r' and value[3] == 'o' and value[4] == 'w':
                return 'throw'
            elif len(value) == 4 and value[1] == 'y' and value[2] == 'p' and value[3] == 'e':
                return 'type'
        
           # ----- Starts with 'u' -----
        if value[0] == 'u':
            # Could be "unique" or "uppercase"
            if len(value) == 6 and value[1] == 'n' and value[2] == 'i' and value[3] == 'q' and value[4] == 'u' and value[5] == 'e':
                return 'unique'
            elif len(value) == 9 and value[1] == 'p' and value[2] == 'p' and value[3] == 'e' and value[4] == 'r' and value[5] == 'c' and value[6] == 'a' and value[7] == 's' and value[8] == 'e':
                return 'uppercase'
            
        # ----- Starts with 'v' -----
        if value[0] == 'v':
            #could be "var"
            if len(value) == 3 and value[1] == 'a' and value[2] == 'r':
                return 'var'
            
        # ----- Starts with 'Y' -----
        if value[0] == 'Y':
            # Could be "YES"
            if len(value) == 3 and value[1] == 'E' and value[2] == 'S':
                return 'STATELITERAL'

        # ----- Starts with 'N' -----
        if value[0] == 'N':
            # Could be "NO"
            if len(value) == 2 and value[1] == 'O':
                return 'STATELITERAL'

        # If nothing matched, it's not a recognized keyword
        return None

    #--------------------------------------------------------------------------
    # Main public method: get_next_token (or the main loop)
    #--------------------------------------------------------------------------
    def get_next_token(self):
        """
        MAIN LOOP: 
        🟢 GOES BACK TO INITIAL STATE AFTER EACH TOKEN
        """
        
        start_line = self.line
        start_column = self.column

        # If we're at the end of the input
        if self.current_char is None:
            return None  # No more tokens

        # Enter the main loop: we read characters until we produce a token
        while self.current_char is not None:
            if self.current_state == LexerState.INITIAL:
                # Handle dash sequences with context awareness
                if self.current_char == '-':
                    peek = self.peek_next_char()
                    
                    # Check for multi-character operators
                    if peek == '-':
                        self.advance()  # first '-'
                        self.advance()  # second '-'
                        self.current_state = LexerState.INITIAL
                        return T('--', '--', start_line, start_column)
                    elif peek == '=':
                        self.advance()  # first '-'
                        self.advance()  # '='
                        self.current_state = LexerState.INITIAL
                        return T('-=', '-=', start_line, start_column)
                    
                    # Check context to determine if this is a negative number or minus operator
                    prev_token_type = self.token_buffer[-1].type if len(self.token_buffer) > 0 else ""
                    
                    # After an identifier, number, or closing bracket/brace/parenthesis, it's a minus operator
                    if (prev_token_type.startswith('IDENTIFIER_') or 
                        prev_token_type in ['INTEGERLITERAL', 'POINTLITERAL', 'NEGINTEGERLITERAL', 'NEGPOINTLITERAL'] or
                        prev_token_type in [')', ']', '}']):
                        self.advance()  # consume '-'
                        self.current_state = LexerState.INITIAL
                        return T('-', '-', start_line, start_column)
                    
                    # Otherwise, if followed by a digit, it's a negative number
                    elif peek and peek.isdigit():
                        self.current_state = LexerState.READING_NEGATIVE_INT
                        continue
                    
                    # Default case: it's a standalone minus operator
                    else:
                        self.advance()
                        self.current_state = LexerState.INITIAL
                        return T('-', '-', start_line, start_column)
                
                # Decide which specialized state to go into, based on current_char
                if self.current_char.isspace():
                    if self.current_char == ' ':
                        self.current_state = LexerState.READING_SPACE
                    elif self.current_char == '\n':
                        self.current_state = LexerState.READING_NEWLINE
                    elif self.current_char == '\t':
                        self.current_state = LexerState.READING_SPACE
                    else:
                        self.advance()
                        return self.get_next_token()
                elif self.current_char == '#':
                    self.current_state = LexerState.READING_COMMENT
                elif self.current_char.isalpha():
                    self.current_state = LexerState.READING_IDENTIFIER
                elif self.current_char.isdigit():
                    self.current_state = LexerState.READING_INT
                elif self.current_char == '"':
                    self.current_state = LexerState.READING_STRING
                elif self.current_char == '.':
                    # Now treat '.' as invalid symbol
                    warning = InvalidSymbolError('.', self.line, self.column)
                    self.errors.append(warning)
                    invalid_char = self.current_char
                    self.advance()

                elif self.current_char in self.symbols:
                    self.current_state = LexerState.READING_SYMBOL
                else:
                    # Invalid symbol => produce warning, return an 'INVALID' token
                    warning = InvalidSymbolError(self.current_char, self.line, self.column)
                    self.errors.append(warning)
                    invalid_char = self.current_char
                    self.advance()
                    return T('INVALID', invalid_char, start_line, start_column, warning="Invalid symbol")

                continue

            #--- Handle each state's logic
            if self.current_state == LexerState.READING_SPACE:
                return self.handle_state_reading_space(start_line, start_column)

            if self.current_state == LexerState.READING_NEWLINE:
                return self.handle_state_reading_newline(start_line, start_column)

            if self.current_state == LexerState.READING_COMMENT:
                return self.handle_state_reading_comment(start_line, start_column)

            if self.current_state == LexerState.READING_IDENTIFIER:
                return self.handle_state_reading_identifier(start_line, start_column)

            if self.current_state == LexerState.READING_INT:
                return self.handle_state_reading_int(start_line, start_column)

            if self.current_state == LexerState.READING_NEGATIVE_INT:
                return self.handle_state_reading_negative_int(start_line, start_column)

            if self.current_state == LexerState.READING_STRING:
                return self.handle_state_reading_string(start_line, start_column)

            if self.current_state == LexerState.READING_SYMBOL:
                return self.handle_state_reading_symbol(start_line, start_column)

        return None  # End of code reached inside the loop

    #--------------------------------------------------------------------------
    # State Handling Routines
    #--------------------------------------------------------------------------

    def handle_state_reading_space(self, start_line, start_column):
        single_char = self.current_char
        self.advance()
        self.current_state = LexerState.INITIAL
        return T('WHITESPACE', single_char, start_line, start_column)

    def handle_state_reading_newline(self, start_line, start_column):
        value = "\\n"
        self.advance()  # consume '\n'
        self.current_state = LexerState.INITIAL
        return T('WHITESPACE', value, start_line, start_column)

    def handle_state_reading_comment(self, start_line, start_column):
        comment_value = ""
        #self.advance()  # skip '#'
        while self.current_char is not None and self.current_char != '\n':
            comment_value += self.current_char
            self.advance()

        self.current_state = LexerState.INITIAL
        return T('COMMENT', comment_value, start_line, start_column)

    def handle_state_reading_identifier(self, start_line, start_column):
        # Check if the first character is valid (allow uppercase for YES and NO)
        if self.current_char not in ATOMS['alphabet']:
            warning_msg = f"Invalid identifier start: '{self.current_char}' - identifiers must start with a letter"
            warning = InvalidIdentifierError(self.current_char, self.line, self.column, warning_msg)
            self.errors.append(warning)
            invalid_char = self.current_char
            self.advance()
            self.current_state = LexerState.INITIAL
            return T('INVALID', invalid_char, start_line, start_column, warning=warning_msg)
        
        # If we reach here, the first character is valid
        value = self.current_char
        self.advance()
        
        # Continue gathering valid characters for the identifier
        # Valid characters include lowercase, uppercase, digits, and underscores
        while self.current_char is not None:
            if (self.current_char.islower() or 
                self.current_char.isupper() or 
                self.current_char.isdigit() or 
                self.current_char == '_'):
                value += self.current_char
                self.advance()
            else:
                break

        # Special check for YES and NO literals before keyword check
        if value == "YES" or value == "NO":
            if self.current_char is not None:
                valid_delims = valid_delimiters_keywords_dict.get('STATELITERAL', [])
                two_char = self.current_char
                if self.peek_next_char():
                    two_char += self.peek_next_char()
                
                # Delimiter check after state literal
                if self.current_char not in valid_delims and two_char not in valid_delims:
                    msg = f"Invalid delimiter after state literal '{value}': '{self.current_char}'"
                    warning = InvalidSymbolError(self.current_char, self.line, self.column)
                    warning.message = msg
                    self.errors.append(warning)
                    self.current_state = LexerState.INITIAL
                    return self.get_next_token()
            
            self.current_state = LexerState.INITIAL
            return T('STATELITERAL', value, start_line, start_column)

        # Check if the gathered value is a keyword (but only for lowercase starting identifiers)
        token_type = None
        if value[0].islower():
            token_type = self.keyword_check(value)
        
        if token_type: #check if token_type has a value
            # -- It's a keyword -- 
            if self.current_char is not None:
                valid_delims = valid_delimiters_keywords_dict.get(token_type, [])
                two_char = self.current_char
                if self.peek_next_char():
                    two_char += self.peek_next_char()
                
                # Delimiter check after a keyword
                if self.current_char not in valid_delims and two_char not in valid_delims:
                    msg = f"Invalid delimiter after keyword '{value}': '{self.current_char}'"
                    warning = InvalidSymbolError(self.current_char, self.line, self.column)
                    warning.message = msg
                    self.errors.append(warning)
                    self.current_state = LexerState.INITIAL
                    return self.get_next_token()

            self.current_state = LexerState.INITIAL
            return T(token_type, value, start_line, start_column)

        else:
            # Not a keyword, check for identifiers
            # Regular identifiers must start with lowercase
            if not value[0].islower():
                warning_msg = f"Invalid identifier '{value}' - identifiers must start with lowercase letter"
                warning = InvalidIdentifierError(value, start_line, start_column, warning_msg)
                self.errors.append(warning)
                self.current_state = LexerState.INITIAL
                return T('INVALID', value, start_line, start_column, warning=warning_msg)
            
            # The identifier is not a keyword, check for length errors
            if len(value) > 20:
                warning_msg = f"Identifier '{value}' exceeds maximum length of 20 characters"
                warning = InvalidIdentifierError(value, start_line, start_column, warning_msg)
                self.errors.append(warning)
                # Return the identifier with a warning instead of skipping it
                self.current_state = LexerState.INITIAL
                return T('INVALID', value, start_line, start_column, warning=warning_msg)

            # Check delimiter for a valid identifier
            if self.current_char is not None:
                two_char = self.current_char
                if self.peek_next_char():
                    two_char += self.peek_next_char()
                
                if (self.current_char not in valid_delimiters_identifier and
                    two_char not in valid_delimiters_identifier):
                    warning_msg = f"Invalid delimiter after identifier '{value}': '{self.current_char}'"
                    warning = InvalidSymbolError(self.current_char, self.line, self.column)
                    warning.message = warning_msg
                    self.errors.append(warning)
                    self.advance()
                    self.current_state = LexerState.INITIAL
                    return self.get_next_token()

            # We have a valid identifier and a valid delimiter.
            identifier_label = self.get_identifier_label(value)
            self.current_state = LexerState.INITIAL
            return T(identifier_label, value, start_line, start_column)

    def handle_state_reading_int(self, start_line, start_column):
        value = ""
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                return self.handle_state_reading_point(value, start_line, start_column)
            value += self.current_char
            self.advance()

        lexeme = value.lstrip('0') or '0'
        if len(lexeme) > 9:
            warning_msg = f"Integer literal '{value}' exceeds max of 9 digits."
            warning = InvalidIntegerError(warning_msg, start_line, start_column)
            self.errors.append(warning)
            self.current_state = LexerState.INITIAL
            return T('INVALID', value, start_line, start_column, warning=warning_msg)

        # Check delimiter
        if self.current_char is not None:
            two_char = self.current_char
            if self.peek_next_char():
                two_char += self.peek_next_char()
            if (self.current_char not in valid_delimiters_numeric and
                two_char not in valid_delimiters_numeric):
                warning_msg = f"Invalid delimiter after integer '{lexeme}': '{self.current_char}'"
                warning = InvalidSymbolError(self.current_char, self.line, self.column)
                warning.message = warning_msg
                self.errors.append(warning)
                # Return the token with a warning instead of skipping it
                self.current_state = LexerState.INITIAL
                return T('INTEGERLITERAL', lexeme, start_line, start_column, warning=warning_msg)

        self.current_state = LexerState.INITIAL
        return T('INTEGERLITERAL', lexeme, start_line, start_column)

    def handle_state_reading_point(self, int_part, start_line, start_column):
        value = int_part + '.'
        self.advance()  # consume '.'
    
        if self.current_char is None or not self.current_char.isdigit():
            warning_msg = "Incomplete point literal."
            warning = InvalidPointError(warning_msg, start_line, start_column)
            self.errors.append(warning)
            self.current_state = LexerState.INITIAL
            return T('INVALID', value, start_line, start_column, error=warning)
    
        # Read all the fractional digits
        fractional_digits = ""
        while self.current_char is not None and self.current_char.isdigit():
            fractional_digits += self.current_char
            self.advance()
        
        # Full value for display in error messages
        full_value = int_part + '.' + fractional_digits
        
        # Check length BEFORE normalization - this is the critical fix
        integer_part_length = len(int_part.lstrip('0') or '0')
        fractional_part_length = len(fractional_digits)  # Don't strip zeros for validation
        
        # Validate the length of both parts
        if integer_part_length > 9 or fractional_part_length > 9:
            warning_msg = f"Point literal '{full_value}' has too many digits before/after decimal."
            error = InvalidPointError(warning_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', full_value, start_line, start_column, error=error)
    
        # Only normalize AFTER validation
        integer_part = int_part.lstrip('0') or '0'
        fractional_part = fractional_digits.rstrip('0') or '0'
        lexeme = integer_part + '.' + fractional_part
    
        # Check delimiter
        if self.current_char is not None and self.current_char not in valid_delimiters_numeric:
            warning_msg = f"Invalid delimiter after point literal '{lexeme}': '{self.current_char}'"
            error = InvalidSymbolError(self.current_char, self.line, self.column)
            error.message = warning_msg
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', lexeme, start_line, start_column, error=error)
    
        self.current_state = LexerState.INITIAL
        return T('POINTLITERAL', lexeme, start_line, start_column)

    def handle_state_reading_negative_int(self, start_line, start_column):
        # We've already determined it's a negative number (- followed by digit)
        prefix = '-'
        self.advance()  # consume '-'
    
        # If the character after prefix is '.' then it's an invalid delimiter.
        if self.current_char == '.':
            warning_msg = f"Invalid delimiter after '{prefix}': '{self.current_char}'"
            warning = InvalidSymbolError(self.current_char, self.line, self.column)
            warning.message = warning_msg
            self.errors.append(warning)
            self.current_state = LexerState.INITIAL
            # Return the prefix token with the warning so that '.' remains for further processing.
            return T('-', prefix, start_line, start_column)
    
        # Otherwise, if it's a digit then continue processing negative numbers.
        if self.current_char is not None and self.current_char.isdigit():
            value = ""
            while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
                if self.current_char == '.':
                    return self.handle_state_reading_negative_point(value, start_line, start_column)
                value += self.current_char
                self.advance()
    
            lexeme = value.lstrip('0') or '0'
            if len(lexeme) > 9:
                warning_msg = f"Negative integer literal '-{value}' exceeds max of 9 digits."
                warning = InvalidIntegerError(warning_msg, start_line, start_column)
                self.errors.append(warning)
                self.current_state = LexerState.INITIAL
                return T('INVALID', value, start_line, start_column, warning=warning_msg)
            
            full_lexeme = '-' + lexeme
    
            # Check delimiter block remains the same
            if self.current_char is not None:
                two_char = self.current_char
                if self.peek_next_char():
                    two_char += self.peek_next_char()
                if (self.current_char not in valid_delimiters_numeric and
                    two_char not in valid_delimiters_numeric):
                    warning_msg = f"Invalid delimiter after negative integer '{full_lexeme}': '{self.current_char}'"
                    warning = InvalidSymbolError(self.current_char, self.line, self.column)
                    warning.message = warning_msg
                    self.errors.append(warning)
                    # Return the token with a warning instead of skipping it
                    self.current_state = LexerState.INITIAL
                    return T('NEGINTEGERLITERAL', full_lexeme, start_line, start_column, warning=warning_msg)
    
            self.current_state = LexerState.INITIAL
            return T('NEGINTEGERLITERAL', full_lexeme, start_line, start_column)
        else:
            # This shouldn't happen because we already checked for a digit in the INITIAL state
            # But handle the edge case anyway
            warning_msg = f"Invalid usage of '-': must be followed by digits."
            warning = InvalidSymbolError('-', start_line, start_column)
            warning.message = warning_msg
            self.errors.append(warning)
            self.current_state = LexerState.INITIAL
            return T('-', '-', start_line, start_column)

    def handle_state_reading_negative_point(self, int_part, start_line, start_column):
        value = int_part + '.'
        self.advance()  # consume '.'
        
        if self.current_char is None or not self.current_char.isdigit():
            warning_msg = "Incomplete negative point literal."
            error = InvalidPointError(warning_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', '-' + value, start_line, start_column, error=error)
        
        fractional_digits = ""
        while self.current_char is not None and self.current_char.isdigit():
            fractional_digits += self.current_char
            self.advance()
        
        full_value = int_part + '.' + fractional_digits
        
        # Check length BEFORE normalization - critical fix
        integer_part_length = len(int_part.lstrip('0') or '0')
        fractional_part_length = len(fractional_digits)  # Don't strip zeros for validation
        
        if integer_part_length > 9 or fractional_part_length > 9:
            warning_msg = f"Negative point literal '-{full_value}' has too many digits before/after decimal."
            error = InvalidPointError(warning_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', '-' + full_value, start_line, start_column, error=error)
    
        # Only normalize AFTER validation
        integer_part = int_part.lstrip('0') or '0'
        fractional_part = fractional_digits.rstrip('0') or '0'
    
        if integer_part == '0' and fractional_part == '0':
            lexeme = f"{integer_part}.{fractional_part}"
            token_type = 'POINTLITERAL'
        else:
            lexeme = f"-{integer_part}.{fractional_part}"
            token_type = 'NEGPOINTLITERAL'
        
        if self.current_char is not None and self.current_char not in valid_delimiters_numeric:
            warning_msg = f"Invalid delimiter after point literal '{lexeme}': '{self.current_char}'"
            error = InvalidSymbolError(self.current_char, self.line, self.column)
            error.message = warning_msg
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', lexeme, start_line, start_column, error=error)
        
        self.current_state = LexerState.INITIAL
        return T(token_type, lexeme, start_line, start_column)

    def handle_state_reading_string(self, start_line, start_column):
        self.advance()  # consume opening quote
        value = '"'
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\':
                value += self.current_char
                self.advance()
                if self.current_char is not None:
                    value += self.current_char
                    self.advance()
            elif self.current_char == '\n':
                # Unterminated string
                break
            else:
                value += self.current_char
                self.advance()

        if self.current_char == '"':
            value += self.current_char
            self.advance()
            self.current_state = LexerState.INITIAL
            return T('TEXTLITERAL', value, start_line, start_column)
        else:
            # Unterminated string
            warning_msg = f"Unterminated string literal: {value}"
            warning = LexerWarning(warning_msg, start_line, start_column, 'Invalid String Literal')
            self.errors.append(warning)
            self.current_state = LexerState.INITIAL
            # CHANGED
            return T('INVALID', value, start_line, start_column, warning=warning_msg)

    def handle_state_reading_symbol(self, start_line, start_column):
        first_char = self.current_char
        symbol = None
        self.advance()

        # Multi-char operators
        if first_char == '+':
            if self.current_char == '+':
                symbol = '++'
                self.advance()
            elif self.current_char == '=':
                symbol = '+='
                self.advance()
            else:
                symbol = '+'
        elif first_char == '-':
            # Check for '--' decrement operator
            if self.current_char == '-':
                symbol = '--'
                self.advance()
            # Check for '-=' assignment operator
            elif self.current_char == '=':
                symbol = '-='
                self.advance()
            # Check if next char is a digit - should not happen due to INITIAL state handling
            elif self.current_char and self.current_char.isdigit():
                # Move back to let INITIAL state handle this
                self.position -= 1
                self.column -= 1
                self.current_char = '-'
                self.current_state = LexerState.INITIAL
                return self.get_next_token()
            else:
                # Regular subtraction operator
                symbol = '-'
        elif first_char == '*':
            if self.current_char == '=':
                symbol = '*='
                self.advance()
            else:
                symbol = '*'
        elif first_char == '/':
            if self.current_char == '=':
                symbol = '/='
                self.advance()
            else:
                symbol = '/'
        elif first_char == '%':
            symbol = '%'
        elif first_char == '=':
            if self.current_char == '=':
                symbol = '=='
                self.advance()
            else:
                symbol = '='
        elif first_char == '!':
            if self.current_char == '=':
                symbol = '!='
                self.advance()
            else:
                symbol = '!'
        elif first_char == '>':
            if self.current_char == '=':
                symbol = '>='
                self.advance()
            else:
                symbol = '>'
        elif first_char == '<':
            if self.current_char == '=':
                symbol = '<='
                self.advance()
            else:
                symbol = '<'
        elif first_char == '&':
            if self.current_char == '&':
                symbol = '&&'
                self.advance()
            else:
                warning_msg = "Invalid symbol: '&'"
                warning = InvalidSymbolError('&', start_line, start_column)
                self.errors.append(warning)
                self.current_state = LexerState.INITIAL
                return T('INVALID', '&', start_line, start_column, warning=warning_msg)
        elif first_char == '|':
            if self.current_char == '|':
                symbol = '||'
                self.advance()
            else:
                warning_msg = "Invalid symbol: '|'"
                warning = InvalidSymbolError('|', start_line, start_column)
                self.errors.append(warning)
                self.current_state = LexerState.INITIAL
                return T('INVALID', '|', start_line, start_column, warning=warning_msg)
        elif first_char in ['{', '}', '(', ')', '[', ']', ':', ',', ';']:
            symbol = first_char
        else:
            # Invalid symbol
            warning_msg = f"Invalid symbol: '{first_char}'"
            warning = InvalidSymbolError(first_char, start_line, start_column)
            self.errors.append(warning)
            self.current_state = LexerState.INITIAL
            return T('INVALID', first_char, start_line, start_column, warning=warning_msg)

        # Now we have the symbol. Validate the delimiter
        if symbol:
            valid_delims = valid_delimiters_symbol_dict.get(symbol, [])
            if self.current_char is not None:
                two_char = self.current_char
                if self.peek_next_char():
                    two_char += self.peek_next_char()
                if (self.current_char not in valid_delims and
                    two_char not in valid_delims):
                    # We'll be more permissive with dash sequences to accommodate user's requirements
                    if symbol in ['-', '--']:
                        self.current_state = LexerState.INITIAL
                        return T(symbol, symbol, start_line, start_column)
                    else:
                        warning_msg = f"Invalid delimiter after symbol '{symbol}': '{self.current_char}'"
                        warning = InvalidSymbolError(self.current_char, self.line, self.column)
                        warning.message = warning_msg
                        self.errors.append(warning)
                        self.current_state = LexerState.INITIAL
                        return T(symbol, symbol, start_line, start_column, warning=warning_msg)

            self.current_state = LexerState.INITIAL
            return T(symbol, symbol, start_line, start_column)

        self.current_state = LexerState.INITIAL
        return None

    #--------------------------------------------------------------------------
    # Utility: token generator
    #--------------------------------------------------------------------------
    def tokenize_all(self):
        """
        Repeatedly calls get_next_token until None is returned.
        Returns a list of tokens.
        """
        self.token_buffer = [] #empty token_buffer to store tokens
        while True: 
            token = self.get_next_token()
            if token is None:
                # End of input
                break
            self.token_buffer.append(token)
        return self.token_buffer