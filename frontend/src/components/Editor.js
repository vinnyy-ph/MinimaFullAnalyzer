// src/components/Editor.js

import React, { useRef, useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { MINIMA, tokenizer, languageConfiguration, updateTokenizerWithBuiltins } from './monacoConfig/languageDefinition';
import { fetchBuiltinFunctions } from './monacoConfig/builtinFunctions';
import { provideCompletionItems } from './monacoConfig/completionProvider';
import { MinimaTheme } from './monacoConfig/theme';
import { MinimaThemeLight } from './monacoConfig/lightTheme'; 
import { useTheme } from '@mui/material/styles';

const CodeEditor = ({ code, setCode }) => {
  const editorRef = useRef(null);
  const theme = useTheme();
  const monacoRef = useRef(null);
  const [isLoadingFunctions, setIsLoadingFunctions] = useState(true);

  const handleEditorChange = (value) => {
    setCode(value);
  };

  // Handle editor mount and setup
  const handleEditorDidMount = (editor, monacoInstance) => {
    editorRef.current = editor;
    monacoRef.current = monacoInstance;
    
    monacoInstance.languages.register({ id: MINIMA });
    monacoInstance.languages.setMonarchTokensProvider(MINIMA, tokenizer);
    monacoInstance.languages.setLanguageConfiguration(MINIMA, languageConfiguration);
    monacoInstance.languages.registerCompletionItemProvider(MINIMA, provideCompletionItems(monacoInstance));

    monacoInstance.editor.defineTheme('myMinimaTheme', MinimaTheme);
    monacoInstance.editor.defineTheme('myMinimaThemeLight', MinimaThemeLight);

    const initialTheme = theme.palette.mode === 'dark' ? 'myMinimaTheme' : 'myMinimaThemeLight';
    monacoInstance.editor.setTheme(initialTheme);
    
    // Once mounted, load the built-in functions
    loadBuiltinFunctions(monacoInstance);
  };

  // Separate function to load built-ins and update the editor
  const loadBuiltinFunctions = async (monacoInstance) => {
    try {
      const functions = await fetchBuiltinFunctions();
      console.log("Fetched built-in functions:", functions);
      
      if (functions && functions.length > 0) {
        // Create a new updated tokenizer
        const updatedTokenizer = updateTokenizerWithBuiltins(functions);
        
        // Apply the updated tokenizer
        monacoInstance.languages.setMonarchTokensProvider(MINIMA, updatedTokenizer);
        
        // Get current model and force re-tokenization
        if (editorRef.current) {
          const model = editorRef.current.getModel();
          if (model) {
            // Force the editor to re-tokenize by temporarily changing the language
            const currentValue = model.getValue();
            
            // Create a new model with the updated language
            const newModel = monacoInstance.editor.createModel(
              currentValue, 
              MINIMA
            );
            
            // Set the editor model to the new model
            editorRef.current.setModel(newModel);
            
            // Dispose of the old model
            model.dispose();
          }
        }
      }
      setIsLoadingFunctions(false);
    } catch (error) {
      console.error("Error loading built-in functions:", error);
      setIsLoadingFunctions(false);
    }
  };

  // Update theme when it changes
  useEffect(() => {
    const monaco = monacoRef.current;
    if (monaco) {
      const themeName = theme.palette.mode === 'dark' ? 'myMinimaTheme' : 'myMinimaThemeLight';
      monaco.editor.setTheme(themeName);
    }
  }, [theme.palette.mode]);

  return (
    <Editor
      height="45vh"
      defaultValue="# Write your code here"
      language={MINIMA}
      theme={theme.palette.mode === 'dark' ? 'myMinimaTheme' : 'myMinimaThemeLight'}
      value={code}
      onChange={handleEditorChange}
      onMount={handleEditorDidMount}
      options={{
        minimap: { enabled: false },
        fontSize: 15,
        fontFamily: 'Fira Code, Consolas, "Courier New", monospace', 
        cursorBlinking: 'smooth',
        cursorSmoothCaretAnimation: true,
        wordWrap: 'on',
        scrollbar: {
          verticalScrollbarSize: 10,
          horizontalScrollbarSize: 10,
          arrowSize: 10,
          verticalHasArrows: false,
          horizontalHasArrows: false,
          scrollbarMinSize: 8,
          renderVerticalScrollbar: 'auto',
          renderHorizontalScrollbar: 'auto',
        },
      }}
    />
  );
};

export default CodeEditor;