import re
from .token_map import TOKEN_MAP

def process_syntax_error(
    error_msg: str,
    line: int = 0,
    column: int = 0,
    expected_tokens=None,
    unexpected_token=None,
    code=""
) -> dict:
    if expected_tokens is None:
        expected_tokens = []

    # Extract the fragment of the code up to the error column
    lines = code.splitlines()
    if 0 < line <= len(lines):
        # Include all previous lines and the current line up to the error column
        preceding_lines = "\n".join(lines[:line-1])
        current_fragment = lines[line - 1][:column]
        line_fragment = preceding_lines + "\n" + current_fragment if preceding_lines else current_fragment
    else:
        line_fragment = code[:column]

    # Function to analyze which brackets are currently open
    def analyze_open_brackets(fragment):
        stack = []
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        
        for ch in fragment:
            if ch in bracket_pairs:  # Opening bracket
                stack.append(ch)
            elif ch in bracket_pairs.values():  # Closing bracket
                # Find matching opening bracket
                for opening, closing in bracket_pairs.items():
                    if ch == closing:
                        # If we have a matching open bracket, pop it
                        if stack and stack[-1] == opening:
                            stack.pop()
                        break
        
        # Return list of currently open brackets
        return stack
    
    # Helper to categorize tokens
    def categorize_tokens(tokens):
        KEYWORDS = {
            "var", "fixed", "group", "func", "throw", "show", "checkif",
            "recheck", "otherwise", "match", "case", "default", "exit",
            "next", "each", "repeat", "do", "integer", "point", "state",
            "text", "empty", "get"
        }
        # Add built-in functions to keywords
        BUILTIN_FUNCTIONS = {
            "abs", "ceil", "contains", "factorial", "floor", "isqrt", "join",
            "length", "lowercase", "max", "min", "pow", "reverse", "round",
            "slice", "sorted", "sum", "type", "unique", "uppercase"
        }
        # Combine regular keywords and built-in functions
        KEYWORDS = KEYWORDS.union(BUILTIN_FUNCTIONS)
        
        # Map for uppercase token versions to lowercase display
        BUILTIN_UPPERCASE_MAP = {
            "ABS": "abs", "CEIL": "ceil", "CONTAINS": "contains", "FACTORIAL": "factorial",
            "FLOOR": "floor", "ISQRT": "isqrt", "JOIN": "join", "LENGTH": "length",
            "LOWERCASE": "lowercase", "MAX": "max", "MIN": "min", "POW": "pow",
            "REVERSE": "reverse", "ROUND": "round", "SLICE": "slice", "SORTED": "sorted",
            "SUM": "sum", "TYPE": "type", "UNIQUE": "unique", "UPPERCASE": "uppercase"
        }
        
        LITERALS = {
            "TEXTLITERAL", "INTEGERLITERAL", "NEGINTEGERLITERAL",
            "POINTLITERAL", "NEGPOINTLITERAL", "STATELITERAL"
        }
        keywords_cat = []
        literals_cat = []
        symbols_cat = []
        others_cat = []
        for token in tokens:
            token_str = str(token)
            
            # Check if the token is a built-in function in uppercase form
            if token_str in BUILTIN_UPPERCASE_MAP:
                keywords_cat.append(BUILTIN_UPPERCASE_MAP[token_str])
            elif token_str in KEYWORDS:
                keywords_cat.append(token_str)
            elif token_str in LITERALS:
                literals_cat.append(token_str)
            elif re.match(r'^[^\w\s]+$', token_str):
                symbols_cat.append(token_str)
            else:
                others_cat.append(token_str)
        return keywords_cat, literals_cat, symbols_cat, others_cat

    # Prioritize grammar violations first (unexpected tokens from the parser)
    unexpected_grammar_error = False
    bracket_pairs = {'(': ')', '[': ']', '{': '}'}
    reverse_pairs = {')': '(', ']': '[', '}': '{'}
    all_brackets = set(bracket_pairs.keys()) | set(bracket_pairs.values())
    
    # Get unexpected token information
    is_end_of_input = False
    if unexpected_token is not None:
        try:
            token_type = unexpected_token.type
            token_value = unexpected_token.value
            mapped_unexpected = TOKEN_MAP.get(token_type, token_value)
            
            # Check if token is end of input/EOF
            if token_type in ['$END', '$EOF'] or mapped_unexpected == "end of input":
                is_end_of_input = True
        except AttributeError:
            token_value = unexpected_token
            mapped_unexpected = TOKEN_MAP.get(unexpected_token, unexpected_token)
            
            # Check if token is end of input/EOF
            if unexpected_token in ['$END', '$EOF'] or mapped_unexpected == "end of input":
                is_end_of_input = True
            
        # Check if our unexpected token is a bracket
        if mapped_unexpected in all_brackets:
            unexpected_grammar_error = True
            # Format a clearer error message for unexpected bracket
            final_message = f"Syntax error at line {line}, column {column}: unexpected '{mapped_unexpected}'"
        elif is_end_of_input:
            unexpected_grammar_error = True
            # Special case for end of input - don't call it a token
            final_message = f"Syntax error at line {line}, column {column}: unexpected end of input"
    else:
        mapped_unexpected = "None"
        token_value = None

    # Map expected tokens using the token map
    mapped_expected = []
    for token in expected_tokens:
        if token in TOKEN_MAP:
            mapped_expected.append(TOKEN_MAP[token])
        else:
            mapped_expected.append(token)

    # If we don't have a direct grammar violation, check for bracket balancing errors
    if not unexpected_grammar_error:
        # Check for unclosed brackets
        open_brackets = analyze_open_brackets(line_fragment)
        
        if open_brackets:
            # There are unclosed brackets - determine which one needs to be closed first
            last_open = open_brackets[-1]
            needed_closer = bracket_pairs[last_open]
            final_message = f"Syntax error at line {line}, column {column}: missing '{needed_closer}'"
        else:
            # No unclosed brackets - standard syntax error
            final_message = f"Syntax error at line {line}, column {column}"
    
    # Filter the expected tokens based on brackets and grammar
    filtered_expected = []
    
    # Analyze which brackets are open in the code fragment
    open_brackets = analyze_open_brackets(line_fragment)
    
    # Filter out closing brackets that don't match any open brackets
    valid_closers = set()
    if open_brackets:
        # Only the most recently opened bracket can be closed next
        valid_closers.add(bracket_pairs[open_brackets[-1]])
    
    # Always keep non-bracket tokens and opening brackets in expected tokens
    # Only filter closing brackets based on the current bracket context
    for token in mapped_expected:
        if token in bracket_pairs.values():  # If token is a closing bracket
            if token in valid_closers:
                filtered_expected.append(token)
        else:
            # For all other tokens (including opening brackets), keep them
            filtered_expected.append(token)

    # Categorize the filtered tokens for display
    keywords_cat, literals_cat, symbols_cat, others_cat = categorize_tokens(filtered_expected)
    
    # Set a flag to indicate if this is an end of input error (used by the frontend)
    is_eof_error = is_end_of_input
    
    return {
        "message": final_message,
        "rawMessage": error_msg,
        "expected": filtered_expected,
        "unexpected": mapped_unexpected,
        "line": line,
        "column": column,
        "value": "",
        "type": "syntax",
        "keywords": keywords_cat,
        "literals": literals_cat,
        "symbols": symbols_cat,
        "others": others_cat,
        "isEndOfInput": is_eof_error
    }