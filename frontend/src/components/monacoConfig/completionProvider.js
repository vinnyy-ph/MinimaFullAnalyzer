// monacoConfig/completionProvider.js
import { fetchBuiltinFunctions } from './builtinFunctions';
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
            insertText: 'switch (${1:expression}) {\n\tcase ${2:1}:\n\t\t${3:# code}\n\tdefault:\n\t\t${4:# code}\n}',
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
          ...builtinSuggestions,
        ];
        return { suggestions };
      }
    };
  };
  function getBuiltinFunctionDocumentation(funcName) {
    const docs = {
      'length': {
        description: 'Returns the number of items in a list or characters in a text string.',
        parameters: [
          { name: 'collection', type: 'list|text', description: 'The list or text to measure' }
        ],
        returns: { type: 'integer', description: 'The number of items or characters' },
        example: 'var myList = [1, 2, 3, 4];\nvar size = length(myList); // Returns 4\nsize = length("Hello"); // Returns 5'
      },
      
      'uppercase': {
        description: 'Converts all characters in a text string to uppercase.',
        parameters: [
          { name: 'text', type: 'text', description: 'The text to convert' }
        ],
        returns: { type: 'text', description: 'The text with all characters in uppercase' },
        example: 'var result = uppercase("Hello"); // Returns "HELLO"'
      },
      
      'lowercase': {
        description: 'Converts all characters in a text string to lowercase.',
        parameters: [
          { name: 'text', type: 'text', description: 'The text to convert' }
        ],
        returns: { type: 'text', description: 'The text with all characters in lowercase' },
        example: 'var result = lowercase("HELLO"); // Returns "hello"'
      },
      
      'max': {
        description: 'Returns the largest value in a list or the largest character in a text string.',
        parameters: [
          { name: 'collection', type: 'list|text', description: 'The list or text to search' }
        ],
        returns: { type: 'dynamic', description: 'The largest value in the collection' },
        example: 'var largest = max([5, 2, 8, 1]); // Returns 8\nvar char = max("abc"); // Returns "c"'
      },
      
      'min': {
        description: 'Returns the smallest value in a list or the smallest character in a text string.',
        parameters: [
          { name: 'collection', type: 'list|text', description: 'The list or text to search' }
        ],
        returns: { type: 'dynamic', description: 'The smallest value in the collection' },
        example: 'var smallest = min([5, 2, 8, 1]); // Returns 1\nvar char = min("abc"); // Returns "a"'
      },
      
      'sorted': {
        description: 'Returns a new sorted list containing all items from the provided collection in ascending order.',
        parameters: [
          { name: 'collection', type: 'list|text', description: 'The list or text to sort' }
        ],
        returns: { type: 'list', description: 'A new sorted list' },
        example: 'var sorted = sorted([3, 1, 4, 2]); // Returns [1, 2, 3, 4]\nvar chars = sorted("dcba"); // Returns ["a", "b", "c", "d"]'
      },
      
      'reverse': {
        description: 'Returns a new collection with all items in reverse order.',
        parameters: [
          { name: 'collection', type: 'list|text', description: 'The list or text to reverse' }
        ],
        returns: { type: 'dynamic', description: 'A new reversed collection of the same type' },
        example: 'var reversed = reverse([1, 2, 3]); // Returns [3, 2, 1]\nvar text = reverse("hello"); // Returns "olleh"'
      },
      
      'abs': {
        description: 'Returns the absolute (positive) value of a number.',
        parameters: [
          { name: 'number', type: 'integer|point', description: 'The number to get absolute value of' }
        ],
        returns: { type: 'integer|point', description: 'The absolute value' },
        example: 'var result = abs(~5); // Returns 5\nresult = abs(~3.14); // Returns 3.14'
      },
      
      'sum': {
        description: 'Returns the sum of all numbers in a list.',
        parameters: [
          { name: 'list', type: 'list', description: 'The list of numbers to sum' }
        ],
        returns: { type: 'integer|point', description: 'The sum of all numbers' },
        example: 'var total = sum([1, 2, 3, 4]); // Returns 10'
      },
      
      'contains': {
        description: 'Checks if an item exists in the specified collection.',
        parameters: [
          { name: 'collection', type: 'list|text', description: 'The list or text to search in' },
          { name: 'item', type: 'any', description: 'The item to search for' }
        ],
        returns: { type: 'state', description: 'YES if item is found, NO otherwise' },
        example: 'var hasIt = contains([1, 2, 3], 2); // Returns YES\nhasIt = contains("Hello", "x"); // Returns NO'
      },
      
      'indexOf': {
        description: 'Returns the index of the first occurrence of an item in a collection.',
        parameters: [
          { name: 'collection', type: 'list|text', description: 'The list or text to search in' },
          { name: 'item', type: 'any', description: 'The item to find' }
        ],
        returns: { type: 'integer', description: 'The index of the item, or -1 if not found' },
        example: 'var pos = indexOf([10, 20, 30], 20); // Returns 1\npos = indexOf("Hello", "l"); // Returns 2'
      },
      
      'join': {
        description: 'Combines all elements in a list into a single text string with a specified separator.',
        parameters: [
          { name: 'separator', type: 'text', description: 'The text to insert between elements' },
          { name: 'list', type: 'list', description: 'The list of items to join' }
        ],
        returns: { type: 'text', description: 'A text string containing all joined elements' },
        example: 'var result = join(", ", [1, 2, 3]); // Returns "1, 2, 3"\nvar csv = join(",", ["a", "b", "c"]); // Returns "a,b,c"'
      },
      
      'slice': {
        description: 'Extracts a portion of a list or text from start index to end index.',
        parameters: [
          { name: 'collection', type: 'list|text', description: 'The list or text to slice' },
          { name: 'start', type: 'integer', description: 'The starting index (inclusive)' },
          { name: 'end', type: 'integer', description: 'The ending index (exclusive)' }
        ],
        returns: { type: 'list|text', description: 'A portion of the original collection' },
        example: 'var part = slice([1, 2, 3, 4, 5], 1, 4); // Returns [2, 3, 4]\nvar substr = slice("Hello", 1, 3); // Returns "el"'
      },
      
      'unique': {
        description: 'Returns a new list containing only unique elements from the original list, preserving order.',
        parameters: [
          { name: 'list', type: 'list|text', description: 'The collection to remove duplicates from' }
        ],
        returns: { type: 'list', description: 'A new list with duplicate elements removed' },
        example: 'var uniq = unique([1, 2, 2, 3, 1, 4]); // Returns [1, 2, 3, 4]\nuniq = unique("hello"); // Returns ["h", "e", "l", "o"]'
      },
      
      'type': {
        description: 'Returns the data type of a value as a text string.',
        parameters: [
          { name: 'value', type: 'any', description: 'The value to check' }
        ],
        returns: { type: 'text', description: 'The type as a text string: "integer", "point", "text", "list", "state", or "empty"' },
        example: 'var t = type(42); // Returns "integer"\nt = type("hello"); // Returns "text"\nt = type([1, 2]); // Returns "list"'
      },
      'isqrt': {
        description: 'Returns the integer square root of a number (largest integer i such that i*i ≤ n).',
        parameters: [
          { name: 'number', type: 'integer|point', description: 'A non-negative number' }
        ],
        returns: { type: 'integer', description: 'The integer square root' },
        example: 'var result = isqrt(16); // Returns 4\nresult = isqrt(10); // Returns 3'
      },
      
      'pow': {
        description: 'Raises a number to the specified power.',
        parameters: [
          { name: 'base', type: 'integer|point', description: 'The base number' },
          { name: 'exponent', type: 'integer|point', description: 'The exponent' }
        ],
        returns: { type: 'integer|point', description: 'The result of base^exponent' },
        example: 'var result = pow(2, 3); // Returns 8\nresult = pow(9, 0.5); // Returns 3'
      },
      
      'factorial': {
        description: 'Calculates the factorial of a non-negative integer (n!).',
        parameters: [
          { name: 'n', type: 'integer', description: 'A non-negative integer (max value: 20)' }
        ],
        returns: { type: 'integer', description: 'The factorial of n' },
        example: 'var result = factorial(5); // Returns 120 (5! = 5*4*3*2*1)'
      },
      
      'ceil': {
        description: 'Returns the smallest integer greater than or equal to the given number.',
        parameters: [
          { name: 'number', type: 'integer|point', description: 'The number to round up' }
        ],
        returns: { type: 'integer', description: 'The ceiling value' },
        example: 'var result = ceil(4.2); // Returns 5\nresult = ceil(~1.8); // Returns ~1'
      },
      
      'floor': {
        description: 'Returns the largest integer less than or equal to the given number.',
        parameters: [
          { name: 'number', type: 'integer|point', description: 'The number to round down' }
        ],
        returns: { type: 'integer', description: 'The floor value' },
        example: 'var result = floor(4.9); // Returns 4\nresult = floor(~1.2); // Returns ~2'
      },
      
      'round': {
        description: 'Rounds a number to the nearest integer or specified decimal places.',
        parameters: [
          { name: 'number', type: 'integer|point', description: 'The number to round' },
          { name: 'places', type: 'integer', description: 'Optional: decimal places (default: 0)' }
        ],
        returns: { type: 'integer|point', description: 'The rounded number' },
        example: 'var result = round(4.5); // Returns 5\nresult = round(3.14159, 2); // Returns 3.14'
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