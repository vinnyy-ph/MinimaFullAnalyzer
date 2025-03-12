// monacoConfig/completionProvider.js

export const provideCompletionItems = (monacoInstance) => {
    return {
      provideCompletionItems: () => {
        const suggestions = [
          { label: 'var', kind: monacoInstance.languages.CompletionItemKind.Keyword, insertText: 'var' },
          { 
            label: 'get', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'get(${1:})', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'show', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'show(${1:})', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'integer', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'integer(${1:})', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'point', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'point(${1:})', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'state', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'state(${1:})', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'text', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'text(${1:})', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'group', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'group ${1:} {\n\t$0\n}',
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'checkif', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'checkif(${1:condition}) {\n\t$0\n}', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'recheck', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'recheck(${1:condition}) {\n\t$0\n}', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'otherwise', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'otherwise {\n\t$0\n}', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'switch', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'switch (${1:expression}) {\n\tcase ${2:value}:\n\t\t${3:# code}\n\tdefault:\n\t\t${4:# code}\n}',
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'each', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'each (${1:i} = 0; ${2:<condition>}; ${1:i}++) {\n\t$0\n}', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'repeat', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'repeat (${1:condition}) {\n\t$0\n}', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'do', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'do {\n\t$0\n} repeat (${1:condition});', 
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { label: 'exit', kind: monacoInstance.languages.CompletionItemKind.Keyword, insertText: 'exit' },
          { label: 'next', kind: monacoInstance.languages.CompletionItemKind.Keyword, insertText: 'next;' },
          { label: 'fixed', kind: monacoInstance.languages.CompletionItemKind.Keyword, insertText: 'fixed' },
          { 
            label: 'func', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'func ${1:}(${2:}) {\n\t$0\n}',
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { label: 'throw', kind: monacoInstance.languages.CompletionItemKind.Keyword, insertText: 'throw' },
          { 
            label: 'case\n\t\t', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'case ${1:}:\n\t',
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { 
            label: 'default', 
            kind: monacoInstance.languages.CompletionItemKind.Keyword, 
            insertText: 'default:\n\t',
            insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet 
          },
          { label: 'YES', kind: monacoInstance.languages.CompletionItemKind.Keyword, insertText: 'YES' },
          { label: 'NO', kind: monacoInstance.languages.CompletionItemKind.Keyword, insertText: 'NO' },
          { label: 'empty', kind: monacoInstance.languages.CompletionItemKind.Keyword, insertText: 'empty' },
        ];
        return { suggestions };
      }
    };
  };