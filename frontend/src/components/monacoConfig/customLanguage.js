// frontend/src/monacoConfig/customLanguage.js
import { MinimaCompletionProvider } from './completionProvider.js';

export const MinimaLang = (monaco) => {
    monaco.languages.register({ id: 'MinimaLanguage' });
  
    monaco.languages.setMonarchTokensProvider('MinimaLanguage', {
      tokenizer: {
        root: [
            [/#[^\n]*/, 'comment'],
          [/[a-z_$][\w$]*/, {
            cases: {
              '@keywords': 'keyword'
            }
          }],
          [/[{}()\[\]]/, 'delimiter'],
          [/"/, { token: 'string.quote', next: '@string' }],
          [/[;,.]/, 'delimiter'],
        ],
        string: [
          [/[^\\"]+/, 'string'],
          [/\\./, 'string.escape.invalid'],
          [/"/, { token: 'string.quote', next: '@pop' }],
        ],
      },
      keywords: ['var','get', 'show', 'integer', 'point', 'state', 'text', 'group', 'checkif', 'recheck', 'otherwise', 'switch', 'each','repeat','do', 'exit','next','fixed','func','throw','case','default','YES','NO', 'empty'],
    });
  
    monaco.languages.setLanguageConfiguration('MinimaLanguage', {
      brackets: [
        ['{', '}'],
        ['[', ']'],
        ['(', ')']
      ],
      autoClosingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"' },
        { open: "'", close: "'" },
      ],
    });
    MinimaCompletionProvider(monaco);
  };