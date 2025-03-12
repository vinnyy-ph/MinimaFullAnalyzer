# lexer_states.py

from enum import Enum, auto

class LexerState(Enum):
    # The "default" state—lexer hasn’t decided what it’s reading yet
    INITIAL = auto()

    # Whitespace / spacing
    READING_SPACE = auto()
    READING_NEWLINE = auto()
    READING_COMMENT = auto()

    # Identifiers and keywords
    READING_IDENTIFIER = auto()

    # Numeric literals
    READING_INT = auto()
    READING_NEGATIVE_INT = auto()
    READING_POINT = auto()
    READING_NEGATIVE_POINT = auto()

    # String literals
    READING_STRING = auto()
    
    # Symbols (including multi-char operators)
    READING_SYMBOL = auto()

    # Special "error" or "final" states can be defined if needed
    ERROR_STATE = auto()
