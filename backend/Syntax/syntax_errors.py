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

    # Extract the fragment of the code up to the error column.
    lines = code.splitlines()
    if 0 < line <= len(lines):
        # Include the character at the error column.
        line_fragment = lines[line - 1][:column]
    else:
        line_fragment = code[:column]

    # Helper to find which bracket is still open (if any).
    def find_last_unmatched_bracket(fragment):
        stack = []
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        openings = bracket_pairs.keys()
        closings = bracket_pairs.values()
        for ch in fragment:
            if ch in openings:
                stack.append(ch)
            elif ch in closings:
                if stack and bracket_pairs[stack[-1]] == ch:
                    stack.pop()
        if stack:
            return bracket_pairs[stack[-1]]
        return None

    # Helper to categorize tokens.
    def categorize_tokens(tokens):
        # Define your categories.
        KEYWORDS = {
            "var", "fixed", "group", "func", "throw", "show", "checkif",
            "recheck", "otherwise", "switch", "case", "default", "exit",
            "next", "each", "repeat", "do", "integer", "point", "state",
            "text", "empty", "get"
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

    missing = find_last_unmatched_bracket(line_fragment)
    if missing is not None:
        final_message = f"Syntax error at line {line}, column {column}: missing {missing}"
        keywords_cat, literals_cat, symbols_cat, others_cat = categorize_tokens([missing])
        return {
            "message": final_message,
            "rawMessage": error_msg,
            "expected": [missing],
            "unexpected": unexpected_token,
            "line": line,
            "column": column,
            "value": "",
            "type": "syntax",
            "keywords": keywords_cat,
            "literals": literals_cat,
            "symbols": symbols_cat,
            "others": others_cat
        }

    # Map the unexpected token if available.
    if unexpected_token is not None:
        try:
            token_type = unexpected_token.type
            mapped_unexpected = TOKEN_MAP.get(token_type, unexpected_token.value)
        except AttributeError:
            mapped_unexpected = TOKEN_MAP.get(unexpected_token, unexpected_token)
    else:
        mapped_unexpected = "None"

    # 1) Map expected tokens using the token map.
    mapped_expected = []
    for token in expected_tokens:
        if token in TOKEN_MAP:
            mapped_expected.append(TOKEN_MAP[token])
        else:
            mapped_expected.append(token)

    # 2) Filter out mismatched bracket closers.
    def filter_mismatched_brackets(expected_list, fragment):
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        openings = bracket_pairs.keys()
        closings = bracket_pairs.values()

        # Build stack to figure out what's still open at this point
        stack = []
        for ch in fragment:
            if ch in openings:
                stack.append(ch)
            elif ch in closings:
                if stack and bracket_pairs[stack[-1]] == ch:
                    stack.pop()

        if not stack:
            # Nothing is unmatched => remove ALL bracket closers from expected
            all_closing = set(bracket_pairs.values())  # {')', ']', '}'}
            return [t for t in expected_list if t not in all_closing]
        else:
            # Some bracket is open => keep only the matching closer
            last_open = stack[-1]
            needed_closer = bracket_pairs[last_open]
            # We still keep all non-bracket tokens
            all_closing = set(bracket_pairs.values())
            filtered = []
            for t in expected_list:
                if t in all_closing:
                    if t == needed_closer:
                        filtered.append(t)
                else:
                    filtered.append(t)
            return filtered

    mapped_expected = filter_mismatched_brackets(mapped_expected, line_fragment)
    keywords_cat, literals_cat, symbols_cat, others_cat = categorize_tokens(mapped_expected)

    # 3) Build the error message
    expected_lines = "\n".join(f"     {t}" for t in mapped_expected)
    final_message = (
        f"Syntax error at line {line}, column {column}.\n"

    )

    return {
        "message": final_message,
        "rawMessage": error_msg,
        "expected": mapped_expected,
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