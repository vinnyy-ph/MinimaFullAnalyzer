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
    { token: 'string', foreground: 'CE9178' },
    { token: 'string.delim', foreground: 'CE9178' },
    { token: 'string.escape', foreground: 'CE9178' },
    { token: 'function', foreground: '569CD6', fontStyle: 'bold' }, // Bright blue for functions
  ],
  colors: {
    'editor.background': '#001524',
  },
};