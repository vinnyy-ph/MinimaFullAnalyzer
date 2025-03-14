valid_delimiters_identifier = [
    ' ', '\n', '\t', ';', ',', ')', '}', '(', '{', '[', ']', ':',
    '=', '+', '-', '*', '/', '%', '!', '>', '<', '&', '|', '#'
]

valid_delimiters_numeric = [
    '\n',' ', '\t', '+', '-', '*', '/', '%', ',', '=', '!',
    '<', '>', ')', ']', '}', ';', ':', '|', '&', '#'
]

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
    'switch': [ ' ', '(' , '#', '\n', '\t'],
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
}

valid_delimiters_symbol_dict = {
    '=':  [' ', '"', '(', '{', '~', 'Y', 'N', '#', '\n', '\t', '!', '[']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '==': [' ', '(', '~', '"', 'Y', 'N','!', '#', '\n', '\t']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '+':  [' ', '(', '~', '"', '#', '\n', '\t', '!', 'Y', 'N']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '++': [' ', ')', ';', '}', ',', '<', '=','>', '#', '\n', '\t', '+', '-', '/','*','%', '!',']'],
    '+=': [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '-':  [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '--': [' ', ')', ';', '}', ',', '<', '=','>', '#', '\n', '\t', '+', '-', '/','*','%', '!',']'],
    '-=': [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '*':  [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '*=': [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '/':  [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '/=': [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '%':  [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '!':  [' ', '(', 'Y', 'N', '#', '\n', '\t','~','!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '!=': [' ', '(', '~', '"', 'Y', 'N','!', '#', '\n', '\t']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '>':  [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '>=': [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '<':  [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '<=': [' ', '(', '~', '#', '\n', '\t', 'Y', 'N', '!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '&&': [' ', '(', 'Y', 'N', '!', '#', '\n', '\t','~']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '||': [' ', '(', 'Y', 'N','!', '#', '\n', '\t','~']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '{':  [' ', '\n', '\t', '"', 'Y', 'N', '~', '(','{','}', '#', '\n', '\t']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '}':  [' ', '\n', '\t', '=', ';','}', ',',')', '#', '\n', '\t','+','-','/','*','%','<','>','!','&','|',']']
        + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '(':  ['!',' ', '~', '"', '(', 'Y', 'N',')', '#', '\n', '\t']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    ')':  [' ', '\n', '\t', ';', ')', '{', '+', '-', '*', '/',
            '%', '=', '!=', '<', '>', '<=', '>=', '&', '|', '!',
            ',', '}', '#', '\n', '\t',']'],
    '[':  [' ', '"','#', '\n', '\t','Y','N','~','(',']'] + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    ']':  [ ']' ,' ', ')', ';', '+', '-', '*', '/', '%', '=', '+', '-',
            '/', '*', '=', '!', '<', '>', '#', '\n', '\t',',','}'],
    ':':  [' ', '\n', '\t', '{', '~', '"', 'Y', 'N', '#', '\n', '\t']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    '~':  ['Y','N',' ', '(', '#','\n','~','!'] + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    ',':  [' ', '\n', '\t', '"', '(', '~', 'Y', 'N','{', '#','!']
            + list('abcdefghijklmnopqrstuvwxyz0123456789'),
    ';':  [' ', '\n', '\t', '#', '}','{']
            + list('abcdefghijklmnopqrstuvwxyz'),
}