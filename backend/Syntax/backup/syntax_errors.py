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
            "text", "empty", "get", 
            # Built-in functions
            "length", "uppercase", "lowercase", "max", "min", "sorted",
            "reverse", "abs", "sum", "contains", "indexOf", "join",
            "slice", "unique", "type", "isqrt", "pow", "factorial",
            "ceil", "floor", "round"
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
            if token_str in KEYWORDS:
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
    if unexpected_token is not None:
        try:
            token_type = unexpected_token.type
            token_value = unexpected_token.value
            mapped_unexpected = TOKEN_MAP.get(token_type, token_value)
        except AttributeError:
            token_value = unexpected_token
            mapped_unexpected = TOKEN_MAP.get(unexpected_token, unexpected_token)
            
        # Check if our unexpected token is a bracket
        if mapped_unexpected in all_brackets:
            unexpected_grammar_error = True
            # Format a clearer error message for unexpected bracket
            final_message = f"Syntax error at line {line}, column {column}: unexpected '{mapped_unexpected}'"
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
    
    # If we have an unexpected token that's a grammar error, filter based on that
    if unexpected_grammar_error:
        # Keep only non-bracket tokens and the expected bracket according to grammar
        for token in mapped_expected:
            if token not in all_brackets or token in expected_tokens:
                filtered_expected.append(token)
    else:
        # Analyze which brackets are open in the code fragment
        open_brackets = analyze_open_brackets(line_fragment)
        
        # Filter out closing brackets that don't match any open brackets
        valid_closers = set()
        if open_brackets:
            # Only the most recently opened bracket can be closed next
            valid_closers.add(bracket_pairs[open_brackets[-1]])
        
        for token in mapped_expected:
            if token in bracket_pairs.values():  # Closing brackets
                if token in valid_closers:
                    filtered_expected.append(token)
            else:
                # Keep all non-bracket tokens
                filtered_expected.append(token)

    # Categorize the filtered tokens for display
    keywords_cat, literals_cat, symbols_cat, others_cat = categorize_tokens(filtered_expected)
    
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
        "others": others_cat
    }