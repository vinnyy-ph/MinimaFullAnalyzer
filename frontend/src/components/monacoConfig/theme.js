// monacoConfig/theme.js

export const MinimaTheme = {
  base: 'vs-dark',
  inherit: true,
  rules: [
    { token: 'comment', foreground: '6A9955' },
    { token: 'keyword', foreground: '569CD6', fontStyle: 'bold' },
    { token: 'identifier', foreground: 'D4D4D4' },
    { token: 'number', foreground: 'B5CEA8' },
    { token: 'operator', foreground: 'D4D4D4' },
    { token: 'delimiter', foreground: 'D4D4D4' },
    { token: 'string', foreground: '6A9955' },
    { token: 'string.delim', foreground: '6A9955' },
    { token: 'string.escape', foreground: '6A9955' },
  ],
  colors: {
    'editor.background': '#001524',
  },
};