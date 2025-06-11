valid_delimiters_identifier = [
    ' ', '\n', '\t', ';', ',', ')', '}', '(', '{', '[', ']', ':',
    '=', '+', '-', '*', '/', '%', '!', '>', '<', '&', '|', '#'
] # a list of delimiters for identifiers

valid_delimiters_numeric = [
    '\n',' ', '\t', '+', '-', '*', '/', '%', ',', '=', '!',
    '<', '>', ')', ']', '}', ';', ':', '|', '&', '#'
] # a list of delimiters for numeric literals

# a dictionary mapping of keywords to their valid delimiters
valid_delimiters_keywords_dict = {
    'get': [ ' ', '(' , '#', '\n', '\t'],
    'show': [ ' ', '(', '#', '\n', '\t' ],
    'integer': [ ' ', '(' , '#', '\n', '\t'],
    'point': [ ' ', '(' , '#', '\n', '\t'],
    'text': [ ' ', '(' , '#', '\n', '\t'],
    'state': [ ' ', '(', '#', '\n', '\t' ],
    'group': [ ' ' , '#', '\n', '\t'],
    'fixed': [ ' ', '#', '\n', '\t'],
    'checkif': [ ' ', '(' ,'\n', '\t', '#'],
    'recheck': [ ' ', '(' ,'\n', '\t', '#'],
    'otherwise': [ ' ', '\n', '\t', '{' , '#'],
    'match': [ ' ', '(' , '#', '\n', '\t'],
    'case': [ ' ' , '#', '\n', '\t'],
    'default': [ ' ', ':' , '#', '\n', '\t'],
    'each': [ ' ', '(', '#', '\n', '\t'],
    'repeat': [ ' ', '(' ,'\n', '\t', '#'],
    'do': [ ' ', '{' ,'', '#', '\n', '\t'],
    'exit': [ ' ', ';' , '#', '\n', '\t'],
    'next': [ ' ', ';' , '#', '\n', '\t'],
    'func': [ ' ' , '#', '\n', '\t'],
    'throw': [ ' ' , '#', '\n', '\t', '(', '"'],
    'empty': [ ' ', ';',',',':' , '#', '\n', '\t',']','}'],
    'var': [ ' ', '#', '\n', '\t'],
    'STATELITERAL': [ ' ', ')', '&', ',', ';', '}', '|', '=', '!','>','<', '+', '-', '*', '/', '%', '#', '\n', '\t',']',':'],
    # Built-in functions
    'length': [ ' ', '(', '#', '\n', '\t' ],
    'uppercase': [ ' ', '(', '#', '\n', '\t' ],
    'lowercase': [ ' ', '(', '#', '\n', '\t' ],
    'max': [ ' ', '(', '#', '\n', '\t' ],
    'min': [ ' ', '(', '#', '\n', '\t' ],
    'sorted': [ ' ', '(', '#', '\n', '\t' ],
    'reverse': [ ' ', '(', '#', '\n', '\t' ],
    'abs': [ ' ', '(', '#', '\n', '\t' ],
    'sum': [ ' ', '(', '#', '\n', '\t' ],
    'contains': [ ' ', '(', '#', '\n', '\t' ],
    'join': [ ' ', '(', '#', '\n', '\t' ],
    'slice': [ ' ', '(', '#', '\n', '\t' ],
    'unique': [ ' ', '(', '#', '\n', '\t' ],
    'type': [ ' ', '(', '#', '\n', '\t' ],
    'isqrt': [ ' ', '(', '#', '\n', '\t' ],
    'pow': [ ' ', '(', '#', '\n', '\t' ],
    'factorial': [ ' ', '(', '#', '\n', '\t' ],
    'ceil': [ ' ', '(', '#', '\n', '\t' ],
    'floor': [ ' ', '(', '#', '\n', '\t' ],
    'round': [ ' ', '(', '#', '\n', '\t' ],
}

# a dictionary mapping of symbols to their valid delimiters
valid_delimiters_symbol_dict = {
    '=':  [' ', '"', '(', '{', '-', 'Y', 'N', '#', '\n', '\t', '!', '[']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '==': [' ', '(', '-', '"', 'Y', 'N','!', '#', '\n', '\t']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '+':  [' ', '(', '-', '"', '#', '\n', '\t', '!', 'Y', 'N']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '++': [' ', ')', ';', '}', ',', '<', '=','>', '#', '\n', '\t', '+', '-', '/','*','%', '!',']'],
    '+=': [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!', '[']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '-':  [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '--': [' ', ')', ';', '}', ',', '<', '=','>', '#', '\n', '\t', '+', '-', '/','*','%', '!',']'],
    '-=': [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '*':  [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '*=': [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '/':  [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '/=': [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '%':  [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '!':  [' ', '(', 'Y', 'N', '#', '\n', '\t','-','!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '!=': [' ', '(', '-', '"', 'Y', 'N','!', '#', '\n', '\t']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '>':  [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '>=': [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '<':  [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '<=': [' ', '(', '-', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '&&': [' ', '(', 'Y', 'N', '!', '#', '\n', '\t','-']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '||': [' ', '(', 'Y', 'N','!', '#', '\n', '\t','-']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '{':  [' ', '\n', '\t', '"', 'Y', 'N', '-', '(','{','}', '#', '\n', '\t']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '}':  [' ', '\n', '\t', '=', ';','}', ',',')', '#', '\n', '\t','+','-','/','*','%','<','>','!','&','|',']']
        + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '(':  ['!',' ', '-', '"', '(', 'Y', 'N',')', '#', '\n', '\t','[']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    ')':  [' ', '\n', '\t', ';', ')', '{', '+', '-', '*', '/',
            '%', '=', '!=', '<', '>', '<=', '>=', '&', '|', '!',
            ',', '}', '#', '\n', '\t',']'],
    '[':  [' ', '"','#', '\n', '\t','Y','N','-','(',']','['] + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    ']':  [ ']' ,' ', ')', ';', '+', '-', '*', '/', '%', '=', '+', '-',
            '/', '*', '=', '!', '<', '>', '#', '\n', '\t',',','}'],
    ':':  [' ', '\n', '\t', '{', '-', '"', 'Y', 'N', '#', '\n', '\t']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    ',':  [' ', '\n', '\t', '"', '(', '-', 'Y', 'N','{', '#','!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    ';':  [' ', '\n', '\t', '#', '}','{']
            + list('abcdefghijklmnopqrstuvwxyz'),
}