// monacoConfig/completionProvider.js
import { fetchBuiltinFunctions } from './builtinFunctions';

export const MinimaCompletionProvider = (monacoInstance) => {
  monacoInstance.languages.registerCompletionItemProvider('MinimaLanguage', getCompletionProvider(monacoInstance));
};

export const provideCompletionItems = (monacoInstance) => {
  return {
    provideCompletionItems: async () => {
      // Get built-in functions
      const builtinFunctions = await fetchBuiltinFunctions();
      
      // Define built-in function suggestions with proper snippet format
      const builtinSuggestions = builtinFunctions.map(func => {
        let snippet;
        
        // Create appropriate snippets based on common function patterns
        switch(func) {
          case 'length':
            snippet = `${func}(\${1:list})`;
            break;
          case 'uppercase':
          case 'lowercase':
            snippet = `${func}(\${1:text})`;
            break;
          case 'max':
          case 'min':
          case 'sorted':
          case 'reverse':
          case 'sum':
          case 'unique':
          case 'abs':
          case 'type':
            snippet = `${func}(\${1:value})`;
            break;
          case 'contains':
          case 'indexOf':
            snippet = `${func}(\${1:collection}, \${2:item})`;
            break;
          case 'join':
            snippet = `${func}(\${1:separator}, \${2:list})`;
            break;
          case 'slice':
            snippet = `${func}(\${1:collection}, \${2:start}, \${3:end})`;
            break;
          case 'toString':
            snippet = `${func}(\${1:value})`;
            break;
            
          case 'toList':
            snippet = `${func}(\${1:text})`;
            break;
            
          case 'isqrt':
            snippet = `${func}(\${1:number})`;
            break;
            
          case 'pow':
            snippet = `${func}(\${1:base}, \${2:exponent})`;
            break;
            
          case 'factorial':
            snippet = `${func}(\${1:n})`;
            break;
            
          case 'ceil':
          case 'floor':
            snippet = `${func}(\${1:number})`;
            break;
            
          case 'round':
            snippet = `${func}(\${1:number}, \${2:decimalPlaces})`;
            break;
            
          default:
            snippet = `${func}(\${1:})`;
        }
        
        return {
          label: func,
          kind: monacoInstance.languages.CompletionItemKind.Function,
          insertText: snippet,
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getBuiltinFunctionDocumentation(func),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          },
        };
      });
      
      const suggestions = [
        { 
          label: 'var', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'var ${1:name} = ${2:value};',
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('var'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'get', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'get(${1:})', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('get'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'show', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'show(${1:})', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('show'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'integer', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'integer(${1:})', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('integer'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'point', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'point(${1:})', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('point'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'state', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'state(${1:})', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('state'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'text', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'text(${1:})', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('text'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'group', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'group ${1:name} {\n\t$0\n}',
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('group'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'checkif', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'checkif(${1:condition}) {\n\t$0\n}', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('checkif'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'recheck', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'recheck(${1:condition}) {\n\t$0\n}', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('recheck'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'otherwise', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'otherwise {\n\t$0\n}', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('otherwise'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'match', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'match (${1:expression}) {\n\tcase ${2:value1}:\n\t\t${3:# code}\n\tdefault:\n\t\t${5:# code}\n}',
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('match'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'each', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'each (${1:i} = 0; ${2:i < 10}; ${1:i}++) {\n\t$0\n}', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('each'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'repeat', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'repeat (${1:condition}) {\n\t$0\n}', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('repeat'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'do', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'do {\n\t$0\n} repeat (${1:condition});', 
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('do'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'exit', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'exit;',
          documentation: {
            value: getKeywordDocumentation('exit'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'next', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'next;',
          documentation: {
            value: getKeywordDocumentation('next'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'fixed', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'fixed ${1:name} = ${2:value};',
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('fixed'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'func', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'func ${1:name}(${2:parameters}) {\n\t$0\n}',
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('func'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'throw', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'throw ${1:value};',
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('throw'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'case', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'case ${1:value}:\n\t${0:# code}',
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('case'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'default', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'default:\n\t${0:# code}',
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: getKeywordDocumentation('default'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'YES', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'YES',
          documentation: {
            value: getKeywordDocumentation('YES'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'NO', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'NO',
          documentation: {
            value: getKeywordDocumentation('NO'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        { 
          label: 'empty', 
          kind: monacoInstance.languages.CompletionItemKind.Keyword, 
          insertText: 'empty',
          documentation: {
            value: getKeywordDocumentation('empty'),
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        // Add comment snippet
        {
          label: 'comment',
          kind: monacoInstance.languages.CompletionItemKind.Snippet,
          insertText: '# ${1:Comment}',
          insertTextRules: monacoInstance.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: {
            value: "### Comment\n\nInserts a single line comment using the # symbol.\n\n#### Example\n```\n# This is a comment\n```",
            isTrusted: true,
            supportThemeIcons: true,
            supportHtml: true
          }
        },
        ...builtinSuggestions,
      ];

      return { suggestions };
    }
  };
}

// Define the completion provider
export const getCompletionProvider = (monacoInstance) => {
  return provideCompletionItems(monacoInstance);
};

// Documentation function for keywords
function getKeywordDocumentation(keyword) {
  const docs = {
    'var': {
      description: 'Keyword used to declare variables. Similar to "let" in JavaScript.',
      example: 'var x = 10;\nvar name = "John";\nvar active = YES;'
    },
    'get': {
      description: 'Reads and stores data provided by the user. Similar to "input" in Python.',
      example: 'var name = get(); # Get user input\nshow("Hello, " + name);'
    },
    'show': {
      description: 'Sends data to be displayed to the user. Similar to "print" in Python.',
      example: 'show("Hello, World!");\nvar x = 10;\nshow(x);'
    },
    'integer': {
      description: 'Typecasts a value to integer data type (whole numbers without decimal places).',
      example: 'var x = integer("42"); # Converts string to integer\nvar y = integer(3.14); # Converts point to integer (3)'
    },
    'point': {
      description: 'Typecasts a value to point data type (numbers with decimal points).',
      example: 'var x = point("3.14"); # Converts string to point\nvar y = point(42); # Converts integer to point (42.0)'
    },
    'state': {
      description: 'Typecasts a value to state data type (boolean, YES or NO).',
      example: 'var x = state(1); # Converts to YES\nvar y = state(0); # Converts to NO\nvar z = state("true"); # Converts to YES'
    },
    'text': {
      description: 'Typecasts a value to text data type (string).',
      example: 'var x = text(42); # Converts to "42"\nvar y = text(YES); # Converts to "YES"'
    },
    'group': {
      description: 'Defines a group data structure (similar to dictionary/object).',
      example: 'group person {\n\tvar name = "John";\n\tvar age = 30;\n}'
    },
    'checkif': {
      description: 'Starts a conditional statement. Executes a code block if the condition is true. Similar to "if" in other languages.',
      example: 'checkif(x > 10) {\n\tshow("x is greater than 10");\n}'
    },
    'recheck': {
      description: 'Checks additional conditions after an initial checkif. Used like "else if" in other languages.',
      example: 'checkif(x > 10) {\n\tshow("x is greater than 10");\n} recheck(x > 5) {\n\tshow("x is greater than 5");\n}'
    },
    'otherwise': {
      description: 'Executes a code block if all previous conditions in a checkif/recheck chain are false. Similar to "else" in other languages.',
      example: 'checkif(x > 10) {\n\tshow("x is greater than 10");\n} otherwise {\n\tshow("x is not greater than 10");\n}'
    },
    'match': {
      description: 'Selects one of several code blocks to execute based on a value.\nSimilar to python\'s match-case statement.',
      example: 'match(day) {\n\tcase "Monday":\n\t\tshow("Start of work week");\n\tcase "Friday":\n\t\tshow("End of work week");\n\tdefault:\n\t\tshow("Another day");\n}'
    },
    'each': {
      description: 'Loop structure for iterating over a range or collection. Similar to "for" in other languages.',
      example: 'each(i = 0; i < 5; i++) {\n\tshow(i);\n}'
    },
    'repeat': {
      description: 'Loop structure that executes as long as a condition is true. Similar to "while" in other languages.',
      example: 'var x = 0;\nrepeat(x < 10) {\n\tshow(x);\n\tx++;\n}'
    },
    'do': {
      description: 'Loop structure that executes at least once before checking condition. Similar to "do-while" in other languages.',
      example: 'var x = 0;\ndo {\n\tshow(x);\n\tx++;\n} repeat(x < 10);'
    },
    'exit': {
      description: 'Terminates the current loop immediately. Similar to "break" in other languages.',
      example: 'repeat(x < 10) {\n\tshow(x);\n\tx++;\n\tcheckif(x == 5) {\n\t\texit;\n\t}\n}'
    },
    'next': {
      description: 'Skips the rest of the current loop iteration and moves to the next iteration. Similar to "continue" in other languages.',
      example: 'each(i = 0; i < 10; i++) {\n\tcheckif(i % 2 == 0) {\n\t\tnext;\n\t}\n\tshow(i); # Only shows odd numbers\n}'
    },
    'fixed': {
      description: 'Defines a constant variable that cannot be modified after initialization. Similar to "const" in JavaScript.',
      example: 'fixed PI = 3.14159;\n# PI = 3; # This would cause an error'
    },
    'func': {
      description: 'Defines a function with a name and code block. Similar to "function" in JavaScript or "def" in Python.',
      example: 'func add(a, b) {\n\tthrow a + b;\n}\n\nvar result = add(5, 3); # result is 8'
    },
    'throw': {
      description: 'Exits a function and optionally returns a value to the caller. Similar to "return" in other languages.',
      example: 'func add(a, b) {\n\tthrow a + b;\n}\n\nvar result = add(5, 3); # result is 8'
    },
    'case': {
      description: 'Defines a possible value in a match statement.',
      example: 'match(day) {\n\tcase "Monday":\n\t\tshow("Start of week");\n}'
    },
    'default': {
      description: 'Specifies the default case in a match statement when no other cases match.',
      example: 'match(day) {\n\tcase "Monday":\n\t\tshow("Start of week");\n\t\tdefault:\n\t\tshow("Another day");\n}'
    },
    'YES': {
      description: 'Logical value representing true. Used in state (boolean) expressions.',
      example: 'var isActive = YES;\ncheckif(isActive) {\n\tshow("Active");\n}'
    },
    'NO': {
      description: 'Logical value representing false. Used in state (boolean) expressions.',
      example: 'var isActive = NO;\ncheckif(isActive) {\n\tshow("Active");\n} otherwise {\n\tshow("Inactive");\n}'
    },
    'empty': {
      description: 'Value representing the absence of a value. Similar to "null" in JavaScript or "None" in Python.',
      example: 'var x = empty;\ncheckif(x == empty) {\n\tshow("x has no value");\n}'
    },
  };

  if (!docs[keyword]) {
    return `Keyword: ${keyword}`;
  }

  const doc = docs[keyword];
  
  // Format the documentation in a VSCode-like style with Markdown
  let formattedDoc = `### ${keyword}\n\n${doc.description}\n\n`;
  
  // Add example if available
  if (doc.example) {
    formattedDoc += '#### Example\n```\n' + doc.example + '\n```';
  }
  
  return formattedDoc;
}

// Documentation function for built-in functions (preserve existing implementation)
function getBuiltinFunctionDocumentation(funcName) {
  const docs = {
    'length': {
      description: 'Returns the number of items in a list or characters in a text string.',
      parameters: [
        { name: 'collection', type: 'list|text', description: 'The list or text to measure' }
      ],
      returns: { type: 'integer', description: 'The number of items or characters' },
      example: 'var myList = [1, 2, 3, 4];\nvar size = length(myList); # Returns 4\nsize = length("Hello"); # Returns 5'
    },
    
    'uppercase': {
      description: 'Converts all characters in a text string to uppercase.',
      parameters: [
        { name: 'text', type: 'text', description: 'The text to convert' }
      ],
      returns: { type: 'text', description: 'The text with all characters in uppercase' },
      example: 'var result = uppercase("Hello"); # Returns "HELLO"'
    },
    
    'lowercase': {
      description: 'Converts all characters in a text string to lowercase.',
      parameters: [
        { name: 'text', type: 'text', description: 'The text to convert' }
      ],
      returns: { type: 'text', description: 'The text with all characters in lowercase' },
      example: 'var result = lowercase("HELLO"); # Returns "hello"'
    },
    
    'max': {
      description: 'Returns the largest value in a list or the largest character in a text string.',
      parameters: [
        { name: 'collection', type: 'list|text', description: 'The list or text to search' }
      ],
      returns: { type: 'dynamic', description: 'The largest value in the collection' },
      example: 'var largest = max([5, 2, 8, 1]); # Returns 8\nvar char = max("abc"); # Returns "c"'
    },
    
    'min': {
      description: 'Returns the smallest value in a list or the smallest character in a text string.',
      parameters: [
        { name: 'collection', type: 'list|text', description: 'The list or text to search' }
      ],
      returns: { type: 'dynamic', description: 'The smallest value in the collection' },
      example: 'var smallest = min([5, 2, 8, 1]); # Returns 1\nvar char = min("abc"); # Returns "a"'
    },
    
    'sorted': {
      description: 'Returns a new sorted list containing all items from the provided collection in ascending order.',
      parameters: [
        { name: 'collection', type: 'list|text', description: 'The list or text to sort' }
      ],
      returns: { type: 'list', description: 'A new sorted list' },
      example: 'var sorted = sorted([3, 1, 4, 2]); # Returns [1, 2, 3, 4]\nvar chars = sorted("dcba"); # Returns ["a", "b", "c", "d"]'
    },
    
    'reverse': {
      description: 'Returns a new collection with all items in reverse order.',
      parameters: [
        { name: 'collection', type: 'list|text', description: 'The list or text to reverse' }
      ],
      returns: { type: 'dynamic', description: 'A new reversed collection of the same type' },
      example: 'var reversed = reverse([1, 2, 3]); # Returns [3, 2, 1]\nvar text = reverse("hello"); # Returns "olleh"'
    },
    
    'abs': {
      description: 'Returns the absolute (positive) value of a number.',
      parameters: [
        { name: 'number', type: 'integer|point', description: 'The number to get absolute value of' }
      ],
      returns: { type: 'integer|point', description: 'The absolute value' },
      example: 'var result = abs(~5); # Returns 5\nresult = abs(~3.14); # Returns 3.14'
    },
    
    'sum': {
      description: 'Returns the sum of all numbers in a list.',
      parameters: [
        { name: 'list', type: 'list', description: 'The list of numbers to sum' }
      ],
      returns: { type: 'integer|point', description: 'The sum of all numbers' },
      example: 'var total = sum([1, 2, 3, 4]); # Returns 10'
    },
    
    'contains': {
      description: 'Checks if an item exists in the specified collection.',
      parameters: [
        { name: 'collection', type: 'list|text', description: 'The list or text to search in' },
        { name: 'item', type: 'any', description: 'The item to search for' }
      ],
      returns: { type: 'state', description: 'YES if item is found, NO otherwise' },
      example: 'var hasIt = contains([1, 2, 3], 2); # Returns YES\nhasIt = contains("Hello", "x"); # Returns NO'
    },
    
    'indexOf': {
      description: 'Returns the index of the first occurrence of an item in a collection.',
      parameters: [
        { name: 'collection', type: 'list|text', description: 'The list or text to search in' },
        { name: 'item', type: 'any', description: 'The item to find' }
      ],
      returns: { type: 'integer', description: 'The index of the item, or -1 if not found' },
      example: 'var pos = indexOf([10, 20, 30], 20); # Returns 1\npos = indexOf("Hello", "l"); # Returns 2'
    },
    
    'join': {
      description: 'Combines all elements in a list into a single text string with a specified separator.',
      parameters: [
        { name: 'separator', type: 'text', description: 'The text to insert between elements' },
        { name: 'list', type: 'list', description: 'The list of items to join' }
      ],
      returns: { type: 'text', description: 'A text string containing all joined elements' },
      example: 'var result = join(", ", [1, 2, 3]); # Returns "1, 2, 3"\nvar csv = join(",", ["a", "b", "c"]); # Returns "a,b,c"'
    },
    
    'slice': {
      description: 'Extracts a portion of a list or text from start index to end index.',
      parameters: [
        { name: 'collection', type: 'list|text', description: 'The list or text to slice' },
        { name: 'start', type: 'integer', description: 'The starting index (inclusive)' },
        { name: 'end', type: 'integer', description: 'The ending index (exclusive)' }
      ],
      returns: { type: 'list|text', description: 'A portion of the original collection' },
      example: 'var part = slice([1, 2, 3, 4, 5], 1, 4); # Returns [2, 3, 4]\nvar substr = slice("Hello", 1, 3); # Returns "el"'
    },
    
    'unique': {
      description: 'Returns a new list containing only unique elements from the original list, preserving order.',
      parameters: [
        { name: 'list', type: 'list|text', description: 'The collection to remove duplicates from' }
      ],
      returns: { type: 'list', description: 'A new list with duplicate elements removed' },
      example: 'var uniq = unique([1, 2, 2, 3, 1, 4]); # Returns [1, 2, 3, 4]\nuniq = unique("hello"); # Returns ["h", "e", "l", "o"]'
    },
    
    'type': {
      description: 'Returns the data type of a value as a text string.',
      parameters: [
        { name: 'value', type: 'any', description: 'The value to check' }
      ],
      returns: { type: 'text', description: 'The type as a text string: "integer", "point", "text", "list", "state", or "empty"' },
      example: 'var t = type(42); # Returns "integer"\nt = type("hello"); # Returns "text"\nt = type([1, 2]); # Returns "list"'
    },
    'isqrt': {
      description: 'Returns the integer square root of a number (largest integer i such that i*i ≤ n).',
      parameters: [
        { name: 'number', type: 'integer|point', description: 'A non-negative number' }
      ],
      returns: { type: 'integer', description: 'The integer square root' },
      example: 'var result = isqrt(16); # Returns 4\nresult = isqrt(10); # Returns 3'
    },
    
    'pow': {
      description: 'Raises a number to the specified power.',
      parameters: [
        { name: 'base', type: 'integer|point', description: 'The base number' },
        { name: 'exponent', type: 'integer|point', description: 'The exponent' }
      ],
      returns: { type: 'integer|point', description: 'The result of base^exponent' },
      example: 'var result = pow(2, 3); # Returns 8\nresult = pow(9, 0.5); # Returns 3'
    },
    
    'factorial': {
      description: 'Calculates the factorial of a non-negative integer (n!).',
      parameters: [
        { name: 'n', type: 'integer', description: 'A non-negative integer (max value: 20)' }
      ],
      returns: { type: 'integer', description: 'The factorial of n' },
      example: 'var result = factorial(5); # Returns 120 (5! = 5*4*3*2*1)'
    },
    
    'ceil': {
      description: 'Returns the smallest integer greater than or equal to the given number.',
      parameters: [
        { name: 'number', type: 'integer|point', description: 'The number to round up' }
      ],
      returns: { type: 'integer', description: 'The ceiling value' },
      example: 'var result = ceil(4.2); # Returns 5\nresult = ceil(~1.8); # Returns ~1'
    },
    
    'floor': {
      description: 'Returns the largest integer less than or equal to the given number.',
      parameters: [
        { name: 'number', type: 'integer|point', description: 'The number to round down' }
      ],
      returns: { type: 'integer', description: 'The floor value' },
      example: 'var result = floor(4.9); # Returns 4\nresult = floor(~1.2); # Returns ~2'
    },
    
    'round': {
      description: 'Rounds a number to the nearest integer or specified decimal places.',
      parameters: [
        { name: 'number', type: 'integer|point', description: 'The number to round' },
        { name: 'places', type: 'integer', description: 'Optional: decimal places (default: 0)' }
      ],
      returns: { type: 'integer|point', description: 'The rounded number' },
      example: 'var result = round(4.5); # Returns 5\nresult = round(3.14159, 2); # Returns 3.14'
    },
    'toString': {
      description: 'Converts a value to its string representation.',
      parameters: [
        { name: 'value', type: 'any', description: 'The value to convert to string' }
      ],
      returns: { type: 'text', description: 'The string representation of the value' },
      example: 'var str = toString(42); # Returns "42"\nstr = toString([1, 2, 3]); # Returns "[1, 2, 3]"'
    },
    'toList': {
      description: 'Converts a text string to a list of characters.',
      parameters: [
        { name: 'text', type: 'text', description: 'The text to convert' }
      ],
      returns: { type: 'list', description: 'A list containing each character' },
      example: 'var chars = toList("hello"); # Returns ["h", "e", "l", "l", "o"]'
    }
  };
  
  if (!docs[funcName]) {
    return `Built-in function: ${funcName}`;
  }
  
  const doc = docs[funcName];
  
  // Format the documentation in a VSCode-like style with Markdown
  let formattedDoc = `### ${funcName}\n\n${doc.description}\n\n`;
  
  // Add parameters section
  if (doc.parameters && doc.parameters.length) {
    formattedDoc += '#### Parameters\n';
    doc.parameters.forEach(param => {
      formattedDoc += `- \`${param.name}\` (${param.type}): ${param.description}\n`;
    });
    formattedDoc += '\n';
  }
  
  // Add return value
  if (doc.returns) {
    formattedDoc += '#### Returns\n';
    formattedDoc += `(${doc.returns.type}): ${doc.returns.description}\n\n`;
  }
  
  // Add example
  if (doc.example) {
    formattedDoc += '#### Example\n```\n' + doc.example + '\n```';
  }
  
  return formattedDoc;
}