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
                # Pattern detection for complex dash sequences
                if self.current_char == '-':
                    # Look ahead for dash patterns
                    peek_sequence = self.peek_dash_sequence()
                    
                    # Check for specific patterns
                    last_token_type = self.token_buffer[-1].type if len(self.token_buffer) > 0 else ""
                    last_token_is_id = last_token_type.startswith('IDENTIFIER_')
                    last_token_is_num = last_token_type in ['INTEGERLITERAL', 'POINTLITERAL']
                    
                    # Check for different dash patterns with identifier or number prefix
                    if last_token_is_id or last_token_is_num:
                        if peek_sequence == '-':  # a-1 case: Just a minus
                            self.advance()  # consume '-'
                            self.current_state = LexerState.INITIAL
                            return T('-', '-', start_line, start_column)
                            
                        elif peek_sequence == '--':  # a-- case: Decrement operator
                            self.advance()  # first '-'
                            self.advance()  # second '-'
                            self.current_state = LexerState.INITIAL
                            return T('--', '--', start_line, start_column)
                            
                        elif peek_sequence == '--D':  # a--1 case: Should be a, -, -1
                            # Return just the first minus, the rest will be handled separately
                            self.advance()  # consume first '-'
                            self.current_state = LexerState.INITIAL
                            return T('-', '-', start_line, start_column)
                            
                        elif peek_sequence == '---D':  # a---1 case: Should be a, --, -, 1
                            # Return the decrement operator first
                            self.advance()  # first '-'
                            self.advance()  # second '-'
                            self.current_state = LexerState.INITIAL
                            return T('--', '--', start_line, start_column)
                            
                        elif peek_sequence == '----D':  # a----1 case: Should be a, --, -, -1
                            # First return the decrement
                            self.advance()  # first '-'
                            self.advance()  # second '-'
                            self.current_state = LexerState.INITIAL
                            return T('--', '--', start_line, start_column)
                    
                    # Special handling for the second part of a----1 sequence
                    # After we've returned the -- token, we need to handle the remaining --1
                    elif last_token_type == '--' and peek_sequence == '--D':
                        # Return a single minus, next token will be -1
                        self.advance()  # consume one '-'
                        self.current_state = LexerState.INITIAL
                        return T('-', '-', start_line, start_column)
                    
                    # Special handling for dash sequences after increment (++)
                    elif last_token_type == '++':
                        if peek_sequence == '-D':  # a++-1 case: Should be a, ++, -, 1
                            # Return just the minus, the digit will be handled separately
                            self.advance()  # consume '-'
                            self.current_state = LexerState.INITIAL
                            return T('-', '-', start_line, start_column)
                        elif peek_sequence == '--D':  # a++--1 case: Should be a, ++, -, -1
                            # Return just the first minus, rest will be handled separately
                            self.advance()  # consume first '-'
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
                elif self.current_char == '-':
                    # Look at the previous token
                    if len(self.token_buffer) > 0:
                        last_token = self.token_buffer[-1]
                        
                        # After a variable or number, treat as minus/subtraction
                        if (last_token.type.startswith('IDENTIFIER_') or 
                            last_token.type == 'INTEGERLITERAL' or 
                            last_token.type in [')', ']', '}']):
                            self.current_state = LexerState.READING_SYMBOL
                            
                        # After a minus, check for either decrement or negative number
                        elif last_token.type == '-':
                            # If the previous token was minus, check for digit
                            if self.peek_next_char() and self.peek_next_char().isdigit():
                                # This should be a negative number (-5)
                                self.current_state = LexerState.READING_NEGATIVE_INT
                            else:
                                # This could be a decrement
                                self.current_state = LexerState.READING_SYMBOL
                                
                        # After decrement, it should be a minus
                        elif last_token.type == '--':
                            # If followed by digit, should be standalone minus
                            if self.peek_next_char() and self.peek_next_char().isdigit():
                                self.advance()  # consume '-'
                                self.current_state = LexerState.INITIAL
                                return T('-', '-', start_line, start_column)
                            else:
                                self.current_state = LexerState.READING_SYMBOL
                        else:
                            # Check if this could be the start of a negative number
                            peek = self.peek_next_char()
                            if peek and peek.isdigit():
                                self.current_state = LexerState.READING_NEGATIVE_INT
                            else:
                                # Otherwise, process as symbol
                                self.current_state = LexerState.READING_SYMBOL
                    else:
                        # At start of input, check if it's a negative number
                        peek = self.peek_next_char()
                        if peek and peek.isdigit():
                            self.current_state = LexerState.READING_NEGATIVE_INT
                        else:
                            self.current_state = LexerState.READING_SYMBOL
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

    # New helper method to look ahead for dash sequences
    def peek_dash_sequence(self, max_length=5):
        """Peek ahead for sequences of dashes and digits."""
        result = ""
        has_digit = False
        for i in range(max_length):
            char = self.peek_next_char(i)
            if char is None:
                break
            if char == '-':
                result += char
            elif char.isdigit() and i > 0:  # Include digits after first character
                # Just record that we found a digit, but don't include it in the pattern
                has_digit = True
                break
            else:
                break
        
        # Add a generic placeholder if we found a digit
        if has_digit:
            result += "D"  # D for "digit"
        
        return result

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
        # Check if the first character is valid (must be lowercase)
        if self.current_char not in ATOMS['alphabet'] or not self.current_char.islower():
            error_msg = f"Invalid identifier start: '{self.current_char}' - identifiers must start with lowercase letter"
            error = InvalidIdentifierError(self.current_char, self.line, self.column, error_msg)
            self.errors.append(error)
            invalid_char = self.current_char
            self.advance()
            self.current_state = LexerState.INITIAL
            return T('INVALID', invalid_char, start_line, start_column, error=error_msg)
        
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
    
        # Check if the gathered value is a keyword
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
            # The identifier is not a keyword, check for length errors
            if len(value) > 20:
                error_msg = f"Identifier '{value}' exceeds maximum length of 20 characters"
                error = InvalidIdentifierError(value, start_line, start_column, error_msg)
                self.errors.append(error)
                # Return the identifier with an error instead of skipping it
                self.current_state = LexerState.INITIAL
                return T('INVALID', value, start_line, start_column, error=error_msg)
    
            # Check delimiter for a valid identifier
            if self.current_char is not None:
                two_char = self.current_char
                if self.peek_next_char():
                    two_char += self.peek_next_char()
                
                if (self.current_char not in valid_delimiters_identifier and
                    two_char not in valid_delimiters_identifier):
                    error_msg = f"Invalid delimiter after identifier '{value}': '{self.current_char}'"
                    error = InvalidSymbolError(self.current_char, self.line, self.column)
                    error.message = error_msg
                    self.errors.append(error)
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
        # We've already determined it's a negative number (- followed by digit)
        prefix = '-'
        self.advance()  # consume '-'
    
        # If the character after prefix is '.' then it's an invalid delimiter.
        if self.current_char == '.':
            error_msg = f"Invalid delimiter after '{prefix}': '{self.current_char}'"
            error = InvalidSymbolError(self.current_char, self.line, self.column)
            error.message = error_msg
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            # Return the prefix token with the error so that '.' remains for further processing.
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
                error_msg = f"Negative integer literal '-{value}' exceeds max of 9 digits."
                error = InvalidIntegerError(error_msg, start_line, start_column)
                self.errors.append(error)
                self.current_state = LexerState.INITIAL
                return T('INVALID', value, start_line, start_column, error=error_msg)
            
            full_lexeme = '-' + lexeme
    
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
            return T('NEGINTEGERLITERAL', full_lexeme, start_line, start_column)
        else:
            # This shouldn't happen because we already checked for a digit in the INITIAL state
            # But handle the edge case anyway
            error_msg = f"Invalid usage of '-': must be followed by digits."
            error = InvalidSymbolError('-', start_line, start_column)
            error.message = error_msg
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('-', '-', start_line, start_column)

    def handle_state_reading_negative_point(self, int_part, start_line, start_column):
        value = int_part + '.'
        self.advance()  # consume '.'
    
        # If there's no digit after '.', it's incomplete
        if self.current_char is None or not self.current_char.isdigit():
            error_msg = "Incomplete negative point literal."
            error = InvalidPointError(error_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', '-' + value, start_line, start_column, error=error_msg)
    
        while self.current_char is not None and self.current_char.isdigit():
            value += self.current_char
            self.advance()
    
        integer_part = int_part.lstrip('0') or '0'
        fractional_part = value.split('.')[-1].rstrip('0') or '0'

        if len(integer_part) > 9 or len(fractional_part) > 9:
            error_msg = f"Negative point literal '-{int_part}.{fractional_part}' has too many digits before/after decimal."
            error = InvalidPointError(error_msg, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
            return T('INVALID', '-' + int_part + '.' + fractional_part, start_line, start_column, error=error_msg)

        # If the value equals 0.0, treat it as a positive point literal
        if integer_part == '0' and fractional_part == '0':
            lexeme = f"{integer_part}.{fractional_part}"
            token_type = 'POINTLITERAL'
        else:
            lexeme = f"-{integer_part}.{fractional_part}"
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
            # Check for '--' decrement operator
            if self.current_char == '-':
                # This will be a decrement operator
                symbol = '--'
                self.advance()
                
                # Special handling for a----5 case
                if self.current_char == '-' and self.peek_next_char() == '-' and self.peek_next_char(2) and self.peek_next_char(2).isdigit():
                    # This is the a----5 case, we already processed the first '--'
                    # The next dash should be a subtraction, followed by a negative number
                    # Don't consume more dashes here - just return the -- token
                    pass
                
            # Check for '-=' assignment operator
            elif self.current_char == '=':
                symbol = '-='
                self.advance()
            # Check for negative number (when followed by a digit)
            elif self.current_char and self.current_char.isdigit():
                # Check the previous token to decide what to do
                prev_token = self.token_buffer[-1] if len(self.token_buffer) > 0 else None
                prev_token_type = prev_token.type if prev_token else ""
                
                # Special handling for a--5 case
                if prev_token and prev_token_type == '-':
                    # We want a--5 to be (a)(-)(-5), so this should be a negative number
                    # Return to position before the digit
                    self.position -= 1
                    self.column -= 1
                    self.current_char = '-'
                    self.current_state = LexerState.READING_NEGATIVE_INT
                    return self.handle_state_reading_negative_int(start_line, start_column) 
                
                # Decide if it's subtraction + number or negative number
                if (len(self.token_buffer) > 0 and 
                    (self.token_buffer[-1].type == 'INTEGERLITERAL' or 
                     self.token_buffer[-1].type.startswith('IDENTIFIER_') or 
                     self.token_buffer[-1].type in [')', ']', '}'])):
                    # It's subtraction, not negative
                    symbol = '-'
                    # Don't consume the digit, it should be part of the next token
                else:
                    # Move back to process this as a negative number
                    self.position -= 1
                    self.column -= 1
                    self.current_char = '-'
                    self.current_state = LexerState.READING_NEGATIVE_INT
                    return self.handle_state_reading_negative_int(start_line, start_column)
            else:
                # This is just a subtraction operator
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
                return T('INVALID', '&', start_line, start_column, error="Invalid symbol")
        elif first_char == '|':
            if self.current_char == '|':
                symbol = '||'
                self.advance()
            else:
                error = InvalidSymbolError('|', start_line, start_column)
                self.errors.append(error)
                self.current_state = LexerState.INITIAL
                return T('INVALID', '|', start_line, start_column, error="Invalid symbol")
        elif first_char in ['{', '}', '(', ')', '[', ']', ':', ',', ';']:
            symbol = first_char
        else:
            # Invalid symbol
            error = InvalidSymbolError(first_char, start_line, start_column)
            self.errors.append(error)
            self.current_state = LexerState.INITIAL
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
                    # We'll be more permissive with dash sequences to accommodate user's requirements
                    if symbol in ['-', '--']:
                        self.current_state = LexerState.INITIAL
                        return T(symbol, symbol, start_line, start_column)
                    else:
                        msg = f"Invalid delimiter after symbol '{symbol}': '{self.current_char}'"
                        error = InvalidSymbolError(self.current_char, self.line, self.column)
                        error.message = msg
                        self.errors.append(error)
                        self.current_state = LexerState.INITIAL
                        return self.get_next_token()

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
        self.token_buffer = []
        while True:
            token = self.get_next_token()
            if token is None:
                # End of input
                break
            self.token_buffer.append(token)
        return self.token_buffer