export const MINIMA = 'MINIMA';

// This will be populated with built-in function names
let builtinFunctionNames = [];

// Function to update tokenizer with built-in functions
export const updateTokenizerWithBuiltins = (functions) => {
  builtinFunctionNames = functions || [];
  
  console.log("Updating tokenizer with built-in functions:", builtinFunctionNames);
  
  // Include built-in functions in the keyword pattern rather than as a separate token type
  const keywordPattern = 'var|get|show|integer|point|state|text|group|checkif|recheck|otherwise|match|each|repeat|do|exit|next|fixed|func|throw|case|default|YES|NO|empty';
  
  // Combine regular keywords with the built-in function names
  const combinedKeywords = builtinFunctionNames.length > 0
    ? `${keywordPattern}|${builtinFunctionNames.join('|')}`
    : keywordPattern;
  
  console.log("Combined keyword pattern includes built-ins");
  
  // Create a new tokenizer with our updated rules
  const updatedTokenizer = {
    ...tokenizer,
    tokenizer: {
      ...tokenizer.tokenizer,
      root: [
        [/#[^\n]*/, 'comment'],
        [/[a-z_$][\w$]*/, {
          cases: {
            [combinedKeywords]: 'keyword', // Use the combined pattern for keywords
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
      ]
    }
  };
  
  return updatedTokenizer;
};

export const tokenizer = {
  tokenizer: {
    root: [
      [/#[^\n]*/, 'comment'],
      [/[a-z_$][\w$]*/, {
        cases: {
          'var|get|show|integer|point|state|text|group|checkif|recheck|otherwise|match|each|repeat|do|exit|next|fixed|func|throw|case|default|YES|NO|empty': 'keyword',
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
    'checkif', 'recheck', 'otherwise', 'match', 'each', 'repeat',
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