from .tokens import Token as T
from .errors import (
    InvalidIdentifierError,
    LexerError,
    InvalidIntegerError,
    InvalidPointError,
    InvalidSymbolError
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
        self.current_lexeme = ""   # Accumulates characters for the current token
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

        self.position += 1
        self.column += 1

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
            elif len(value) == 7 and value[1] == 'n' and value[2] == 'd' and value[3] == 'e' and value[4] == 'x' and value[5] == 'O' and value[6] == 'f':
                return 'indexOf'
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
            # Could be "show", "state", "switch", "sorted", "sum", "slice"
            if len(value) == 4 and value[1] == 'h' and value[2] == 'o' and value[3] == 'w':
                return 'show'
            elif len(value) == 5 and value[1] == 't' and value[2] == 'a' and value[3] == 't' and value[4] == 'e':
                return 'state'
            elif len(value) == 6 and value[1] == 'w' and value[2] == 'i' and value[3] == 't' and value[4] == 'c' and value[5] == 'h':
                return 'switch'
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
    # Main public method: get_next_token
    #--------------------------------------------------------------------------
    def get_next_token(self):
        """
        MAIN LOOP: 
        🟢 GOES BACK TO INITIAL STATE AFTER EACH TOKEN
        """
        
        self.current_lexeme = ""
        start_line = self.line
        start_column = self.column

        # If we're at the end of the input
        if self.current_char is None:
            return None  # No more tokens

        # Enter the main loop: we read characters until we produce a token
        while self.current_char is not None:
            if self.current_state == LexerState.INITIAL:
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
                elif self.current_char == '~':
                    self.current_state = LexerState.READING_NEGATIVE_INT
                elif self.current_char == '"':
                    self.current_state = LexerState.READING_STRING
                elif self.current_char == '.':
                    # Now treat '.' as invalid symbol
                    error = InvalidSymbolError('.', self.line, self.column)
                    self.errors.append(error)
                    invalid_char = self.current_char
                    self.advance()

                elif self.current_char in self.symbols:
                    self.current_state = LexerState.READING_SYMBOL
                else:
                    # Invalid symbol => produce error, return an 'INVALID' token
                    error = InvalidSymbolError(self.current_char, self.line, self.column)
                    self.errors.append(error)
                    invalid_char = self.current_char
                    self.advance()
                    return T('INVALID', invalid_char, start_line, start_column, error="Invalid symbol")

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
        value = ""
        # 1. Gather all valid characters for the identifier
        while self.current_char is not None:
            if self.current_char in ATOMS['alphanumeric'] or self.current_char == '_':
                value += self.current_char
                self.advance()
            else:
                break
    
        # New check for invalid character that didn't match any valid identifier char.
        if not value:
            msg = f"Invalid character '{self.current_char}' encountered"
            error = InvalidSymbolError(self.current_char, self.line, self.column)
            error.message = msg
            self.errors.append(error)
            self.advance()
            self.current_state = LexerState.INITIAL
            return self.get_next_token()
            
        # 2. Check if the gathered value is a keyword
        token_type = self.keyword_check(value)
        if token_type:
            # -- It's a keyword --
            if self.current_char is not None:
                valid_delims = valid_delimiters_keywords_dict.get(token_type, [])
                two_char = self.current_char
                if self.peek_next_char():
                    two_char += self.peek_next_char()
                
                # Delimiter check after a keyword
                if self.current_char not in valid_delims and two_char not in valid_delims:
                    msg = f"Invalid delimiter after keyword '{value}': '{self.current_char}'"
                    error = InvalidSymbolError(self.current_char, self.line, self.column)
                    error.message = msg
                    self.errors.append(error)
                    self.current_state = LexerState.INITIAL
                    return self.get_next_token()
    
            self.current_state = LexerState.INITIAL
            return T(token_type, value, start_line, start_column)
    
        else:
            # 3. Not a keyword => treat as identifier
            errors_in_identifier = []
            
            if not value or not value[0].islower():
                errors_in_identifier.append("must start with a lowercase letter")
            if len(value) > 20:
                errors_in_identifier.append("cannot exceed 20 characters")
    
            if errors_in_identifier:
                # Invalid identifier
                error_msg = f"Invalid identifier '{value}': " + "; ".join(errors_in_identifier)
                error = InvalidIdentifierError(value, start_line, start_column)
                error.message = error_msg
                self.errors.append(error)
                self.current_state = LexerState.INITIAL
                return self.get_next_token()
    
            else:
                # 4. Check delimiter for a valid identifier
                if self.current_char is not None:
                    two_char = self.current_char
                    if self.peek_next_char():
                        two_char += self.peek_next_char()
                    
                    if (self.current_char not in valid_delimiters_identifier and
                        two_char not in valid_delimiters_identifier):
                        error_msg = (
                            f"Invalid delimiter after identifier '{value}': '{self.current_char}'"
                        )
                        error = InvalidSymbolError(self.current_char, self.line, self.column)
                        error.message = error_msg
                        self.errors.append(error)
                        self.advance()
                        self.current_state = LexerState.INITIAL
                        return self.get_next_token()
    
                # 5. We have a valid identifier and a valid delimiter.
                #    Get or create a numeric label for this identifier.
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
            error_msg = f"Integer literal '{value}' exceeds max of 9 digits."
            error = InvalidIntegerError(error_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return self.get_next_token()

        # Check delimiter
        if self.current_char is not None:
            two_char = self.current_char
            if self.peek_next_char():
                two_char += self.peek_next_char()
            if (self.current_char not in valid_delimiters_numeric and
                two_char not in valid_delimiters_numeric):
                error_msg = f"Invalid delimiter after integer '{lexeme}': '{self.current_char}'"
                error = InvalidSymbolError(self.current_char, self.line, self.column)
                error.message = error_msg
                self.errors.append(error)
                self.current_state = LexerState.INITIAL
                return self.get_next_token()

        self.current_state = LexerState.INITIAL
        return T('INTEGERLITERAL', lexeme, start_line, start_column)

    def handle_state_reading_point(self, int_part, start_line, start_column):
        value = int_part + '.'
        self.advance()  # consume '.'

        if self.current_char is None or not self.current_char.isdigit():
            error_msg = "Incomplete point literal."
            error = InvalidPointError(error_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', value, start_line, start_column, error=error_msg)

        while self.current_char is not None and self.current_char.isdigit():
            value += self.current_char
            self.advance()

        fractional_part = value.split('.')[-1]

        integer_part = value.split('.')[0].lstrip('0') or '0'
        fractional_part = fractional_part.rstrip('0') or '0'

        if len(integer_part) > 9 or len(fractional_part) > 9:
            error_msg = f"Point literal '{value}' has too many digits before/after decimal."
            error = InvalidPointError(error_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return self.get_next_token()

        lexeme = integer_part + '.' + fractional_part

        # Check delimiter
        # if self.current_char is not None:
        #     two_char = self.current_char
        #     if self.peek_next_char():
        #         two_char += self.peek_next_char()
        #     if (self.current_char not in valid_delimiters_numeric and
        #         two_char not in valid_delimiters_numeric):
        #         error_msg = f"Invalid delimiter after point literal '{lexeme}': '{self.current_char}'"
        #         error = InvalidSymbolError(self.current_char, self.line, self.column)
        #         error.message = error_msg
        #         self.errors.append(error)
        #         self.current_state = LexerState.INITIAL
        #         return self.get_next_token()
        if self.current_char is not None:
            if (self.current_char not in valid_delimiters_numeric):
                error_msg = f"Invalid delimiter after point literal '{lexeme}': '{self.current_char}'"
                error = InvalidSymbolError(self.current_char, self.line, self.column)
                error.message = error_msg
                self.errors.append(error)
                self.current_state = LexerState.INITIAL
                return self.get_next_token()

        self.current_state = LexerState.INITIAL
        return T('POINTLITERAL', lexeme, start_line, start_column)

    def handle_state_reading_negative_int(self, start_line, start_column):
        self.advance()  # consume '~'
    
        # If the character after '~' is '.' then it's an invalid delimiter.
        if self.current_char == '.':
            error_msg = f"Invalid delimiter after '~': '{self.current_char}'"
            error = InvalidSymbolError(self.current_char, self.line, self.column)
            error.message = error_msg
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            # Return the '~' token with the error so that '.' remains for further processing.
            return self.get_next_token()
    
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
                error_msg = f"Negative integer literal '~{value}' exceeds max of 9 digits."
                error = InvalidIntegerError(error_msg, start_line, start_column)
                self.errors.append(error)
                self.current_state = LexerState.INITIAL
                return T('INVALID', value, start_line, start_column, error=error_msg)
            
            full_lexeme = '~' + lexeme
    
            # Check delimiter block remains the same
            if self.current_char is not None:
                two_char = self.current_char
                if self.peek_next_char():
                    two_char += self.peek_next_char()
                if (self.current_char not in valid_delimiters_numeric and
                    two_char not in valid_delimiters_numeric):
                    error_msg = f"Invalid delimiter after negative integer '{full_lexeme}': '{self.current_char}'"
                    error = InvalidSymbolError(self.current_char, self.line, self.column)
                    error.message = error_msg
                    self.errors.append(error)
                    self.current_state = LexerState.INITIAL
                    return self.get_next_token()
    
            self.current_state = LexerState.INITIAL
            return self.get_next_token()
        else:
            # Could be symbol '~' if followed by valid delimiter; unchanged.
            valid_delims = valid_delimiters_symbol_dict.get('~', [])
            if self.current_char is not None and self.current_char in valid_delims:
                self.current_state = LexerState.INITIAL
                return T('~', '~', start_line, start_column)
            else:
                if self.current_char is None:
                    error_msg = f"Invalid usage of '~': must be followed by digits or valid delimiter."
                    error = InvalidIntegerError(error_msg, start_line, start_column)
                    self.errors.append(error)
                    self.advance()
                    self.current_state = LexerState.INITIAL
                    return self.get_next_token()
                else:
                    error_msg = f"Invalid delimiter after '~': '{self.current_char}'"
                    error = InvalidSymbolError(self.current_char, self.line, self.column)
                    error.message = error_msg
                    self.errors.append(error)
                    self.current_state = LexerState.INITIAL
                    return self.get_next_token()

    def handle_state_reading_negative_point(self, int_part, start_line, start_column):
        value = int_part + '.'
        self.advance()  # consume '.'
    
        # If there's no digit after '.', it's incomplete
        if self.current_char is None or not self.current_char.isdigit():
            error_msg = "Incomplete negative point literal."
            error = InvalidPointError(error_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', '~' + value, start_line, start_column, error=error_msg)
    
        while self.current_char is not None and self.current_char.isdigit():
            value += self.current_char
            self.advance()
    
        integer_part = int_part.lstrip('0') or '0'
        fractional_part = value.split('.')[-1].rstrip('0') or '0'

        if len(integer_part) > 9 and len(fractional_part) > 9:
            error_msg = f"Negative point literal '~{int_part}.{fractional_part}' exceeds max of 9 integer and fractional digits."
            error = InvalidPointError(error_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', '~' + int_part + '.' + fractional_part, start_line, start_column, error=error_msg)
    
        if len(integer_part) > 9:
            error_msg = f"Negative point literal '~{int_part}.{fractional_part}' exceeds max of 9 integer digits."
            error = InvalidPointError(error_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', '~' + int_part + '.' + fractional_part, start_line, start_column, error=error_msg)
        
        if len(fractional_part) > 9:
            error_msg = f"Negative point literal '~{int_part}.{fractional_part}' exceeds max of 9 fractional digits."
            error = InvalidPointError(error_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', '~' + int_part + '.' + fractional_part, start_line, start_column, error=error_msg)

        # If the value equals 0.0, treat it as a positive point literal
        if integer_part == '0' and fractional_part == '0':
            lexeme = f"{integer_part}.{fractional_part}"
            token_type = 'POINTLITERAL'
        else:
            lexeme = f"~{integer_part}.{fractional_part}"
            token_type = 'NEGPOINTLITERAL'
    
        # Check delimiter
        if self.current_char is not None:
            if (self.current_char not in valid_delimiters_numeric):
                error_msg = f"Invalid delimiter after point literal '{lexeme}': '{self.current_char}'"
                error = InvalidSymbolError(self.current_char, self.line, self.column)
                error.message = error_msg
                self.errors.append(error)
                self.current_state = LexerState.INITIAL
                return self.get_next_token()
    
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
            error_msg = f"Unterminated string literal: {value}"
            error = LexerError(error_msg, start_line, start_column, 'Invalid String Literal')
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            # CHANGED
            return T('INVALID', value, start_line, start_column, error=error_msg)

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
            if self.current_char == '-':
                symbol = '--'
                self.advance()
            elif self.current_char == '=':
                symbol = '-='
                self.advance()
            else:
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
                error = InvalidSymbolError('&', start_line, start_column)
                self.errors.append(error)
                self.current_state = LexerState.INITIAL
                # CHANGED
                return T('INVALID', '&', start_line, start_column, error="Invalid symbol")
        elif first_char == '|':
            if self.current_char == '|':
                symbol = '||'
                self.advance()
            else:
                error = InvalidSymbolError('|', start_line, start_column)
                self.errors.append(error)
                self.current_state = LexerState.INITIAL
                # CHANGED
                return T('INVALID', '|', start_line, start_column, error="Invalid symbol")
        elif first_char in ['{', '}', '(', ')', '[', ']', ':', ',', ';']:
            symbol = first_char
        else:
            # Invalid symbol
            error = InvalidSymbolError(first_char, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            # CHANGED
            return self.get_next_token()

        # Now we have the symbol. Validate the delimiter
        if symbol:
            valid_delims = valid_delimiters_symbol_dict.get(symbol, [])
            if self.current_char is not None:
                two_char = self.current_char
                if self.peek_next_char():
                    two_char += self.peek_next_char()
                if (self.current_char not in valid_delims and
                    two_char not in valid_delims):
                    msg = f"Invalid delimiter after symbol '{symbol}': '{self.current_char}'"
                    error = InvalidSymbolError(self.current_char, self.line, self.column)
                    error.message = msg
                    self.errors.append(error)
                    self.current_state = LexerState.INITIAL
                    return self.get_next_token()

        # if symbol:
        #     valid_delims = valid_delimiters_symbol_dict.get(symbol, [])
        #     if self.current_char is not None:
        #         if (self.current_char not in valid_delims):
        #             msg = f"Invalid delimiter after symbol '{symbol}': '{self.current_char}'"
        #             error = InvalidSymbolError(self.current_char, self.line, self.column)
        #             error.message = msg
        #             self.errors.append(error)
        #             self.current_state = LexerState.INITIAL
        #             return self.get_next_token()

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
        tokens = []
        while True:
            token = self.get_next_token()
            if token is None:
                # End of input
                break
            tokens.append(token)
        return tokens