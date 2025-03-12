export const MINIMA = 'MINIMA';

export const tokenizer = {
  tokenizer: {
    root: [
      [/#[^\n]*/, 'comment'],
      [/[a-z_$][\w$]*/, {
        cases: {
          'var|get|show|integer|point|state|text|group|checkif|recheck|otherwise|switch|each|repeat|do|exit|next|fixed|func|throw|case|default|YES|NO|empty': 'keyword',
          '@default': 'identifier'
        }
      }],
      [/[{}()\[\]]/, '@brackets'],
      [/@symbols/, {
        cases: {
          '@operators': 'operator',
          '@default': ''
        }
      }],
      [/\d+/, 'number'],
      [/[;,.]/, 'delimiter'],
      [/"([^"\\]|\\.)*"/, 'string'],
      [/'([^'\\]|\\.)*'/, 'string'],
    ],
  },
  keywords: [
    'var', 'get', 'show', 'integer', 'point', 'state', 'text', 'group',
    'checkif', 'recheck', 'otherwise', 'switch', 'each', 'repeat',
    'do', 'exit', 'next', 'fixed', 'func', 'throw', 'case', 'default',
    'YES', 'NO', 'empty'
  ],
  operators: [
    '=', '>', '<', '!', '~', '?', ':', '==', '!=', '<=', '>=',
    '&&', '||', '++', '--', '+', '-', '*', '/', '&', '|', '^',
    '%', '<<', '>>', '>>>'
  ],
  symbols: /[=><!~?:&|+\-*\/\^%]+/,
};


export const languageConfiguration = {
  comments: {
    lineComment: '#',
  },
  brackets: [
    ['{', '}'],
    ['[', ']'],
    ['(', ')'],
  ],
  autoClosingPairs: [
    { open: '{', close: '}' },
    { open: '[', close: ']' },
    { open: '(', close: ')' },
    { open: '"', close: '"' },
    { open: "'", close: "'" },
  ],
};