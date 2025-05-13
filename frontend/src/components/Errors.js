import React, { useRef, useEffect, useState, useContext } from 'react';
import { 
  Alert, 
  AlertTitle, 
  Box, 
  Typography, 
  useTheme, 
  Divider, 
  Paper,
  Chip,
  Tabs,
  Tab,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import TerminalIcon from '@mui/icons-material/Terminal';
import CodeIcon from '@mui/icons-material/Code';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

// Create a context for editor reference if it doesn't exist already
// You may need to create this elsewhere in your app
// import { EditorContext } from '../context/EditorContext';

const Errors = ({ errors, terminalOutput = '', debugMode }) => {
  const theme = useTheme();
  const boxRef = useRef(null);
  const [tabIndex, setTabIndex] = useState(0);
  // Uncomment if you have an editor context
  // const { editorRef } = useContext(EditorContext);

  useEffect(() => {
    if (boxRef.current) {
      boxRef.current.scrollTop = 0;
    }
  }, [errors, tabIndex, terminalOutput]);

  // Reset to errors tab if user has terminal tab selected but debug mode gets turned off
  useEffect(() => {
    if (!debugMode && tabIndex === 1) {
      setTabIndex(0);
    }
  }, [debugMode, tabIndex]);

  const lexicalErrors = errors.filter((error) => error.type === 'lexical');
  const syntaxErrors = errors.filter((error) => error.type === 'syntax');
  const semanticErrors = errors.filter((error) => error.type === 'semantic');

  const handleTabChange = (event, newValue) => {
    // Only allow changing to terminal tab if debug mode is on
    if (newValue === 0 || (newValue === 1 && debugMode)) {
      setTabIndex(newValue);
    }
  };

  const hasErrors = errors.length > 0;

  // Helper to determine error type color
  const getErrorTypeColor = (type) => {
    switch(type) {
      case 'lexical': return theme.palette.mode === 'dark' ? '#ff9800' : '#e65100'; // Orange
      case 'syntax': return theme.palette.mode === 'dark' ? '#f44336' : '#b71c1c';  // Red
      case 'semantic': return theme.palette.mode === 'dark' ? '#2196f3' : '#0d47a1'; // Blue
      default: return theme.palette.text.primary;
    }
  };

  // Helper to get background color for error badges
  const getErrorBgColor = (type) => {
    switch(type) {
      case 'lexical': return theme.palette.mode === 'dark' ? 'rgba(255, 152, 0, 0.2)' : 'rgba(255, 152, 0, 0.1)';
      case 'syntax': return theme.palette.mode === 'dark' ? 'rgba(244, 67, 54, 0.2)' : 'rgba(244, 67, 54, 0.1)';
      case 'semantic': return theme.palette.mode === 'dark' ? 'rgba(33, 150, 243, 0.2)' : 'rgba(33, 150, 243, 0.1)';
      default: return 'transparent';
    }
  };

  // Render expected token categories if present
  const renderExpectedCategories = (error) => {
    const { literals, keywords, symbols, others } = error;
    if (!literals?.length && !keywords?.length && !symbols?.length && !others?.length) {
      return null;
    }

    return (
      <Box sx={{ pl: 2, pt: 1 }}>
        {literals?.length > 0 && (
          <Box sx={{ mb: 0.5 }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 'medium' }}>
              Literals:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
              {literals.map((literal, idx) => (
                <Chip 
                  key={idx} 
                  label={literal} 
                  size="small" 
                  sx={{ 
                    backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
                    height: '20px',
                    '& .MuiChip-label': {
                      px: 1,
                      fontSize: '0.7rem'
                    }
                  }} 
                />
              ))}
            </Box>
          </Box>
        )}

        {keywords?.length > 0 && (
          <Box sx={{ mb: 0.5 }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 'medium' }}>
              Keywords:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
              {keywords.map((keyword, idx) => (
                <Chip 
                  key={idx} 
                  label={keyword} 
                  size="small" 
                  sx={{ 
                    backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
                    height: '20px',
                    '& .MuiChip-label': {
                      px: 1,
                      fontSize: '0.7rem'
                    }
                  }} 
                />
              ))}
            </Box>
          </Box>
        )}

        {symbols?.length > 0 && (
          <Box sx={{ mb: 0.5 }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 'medium' }}>
              Symbols:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
              {symbols.map((symbol, idx) => (
                <Chip 
                  key={idx} 
                  label={symbol} 
                  size="small" 
                  sx={{ 
                    backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
                    height: '20px',
                    '& .MuiChip-label': {
                      px: 1,
                      fontSize: '0.7rem'
                    }
                  }} 
                />
              ))}
            </Box>
          </Box>
        )}

        {others?.length > 0 && (
          <Box sx={{ mb: 0.5 }}>
            <Typography variant="caption" sx={{ color: theme.palette.text.secondary, fontWeight: 'medium' }}>
              Others:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
              {others.map((other, idx) => (
                <Chip 
                  key={idx} 
                  label={other} 
                  size="small" 
                  sx={{ 
                    backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
                    height: '20px',
                    '& .MuiChip-label': {
                      px: 1,
                      fontSize: '0.7rem'
                    }
                  }} 
                />
              ))}
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  // Function to jump to error location in editor
  const jumpToErrorLocation = (line, column) => {
    // Check if we have access to the editor
    if (window.monaco && window.editor) {
      try {
        console.log(`Jumping to line ${line}, column ${column}`);
        
        // Convert to numbers to ensure proper handling
        const lineNumber = parseInt(line, 10);
        const columnNumber = parseInt(column, 10);
        
        if (isNaN(lineNumber) || isNaN(columnNumber)) {
          console.error(`Invalid line or column values: line=${line}, column=${column}`);
          return;
        }
        
        // Ensure the editor has a valid model
        const model = window.editor.getModel();
        if (!model) {
          console.error('Editor has no model');
          return;
        }
        
        // Check if the line is within the bounds of the document
        const lineCount = model.getLineCount();
        if (lineNumber > lineCount) {
          console.warn(`Line ${lineNumber} is out of bounds (max: ${lineCount})`);
          return;
        }
        
        // Monaco uses 1-based line numbers and 1-based column numbers
        window.editor.revealPositionInCenter({
          lineNumber: lineNumber,
          column: columnNumber
        });
        
        // Set selection at the error position with a wider selection for visibility
        window.editor.setSelection({
          startLineNumber: lineNumber,
          startColumn: Math.max(1, columnNumber - 1),
          endLineNumber: lineNumber,
          endColumn: columnNumber + 2
        });
        
        // Add a highlighted decoration to make the error location more visible
        const decorations = window.editor.deltaDecorations([], [
          {
            range: {
              startLineNumber: lineNumber,
              startColumn: Math.max(1, columnNumber - 1),
              endLineNumber: lineNumber,
              endColumn: columnNumber + 2
            },
            options: {
              className: 'error-highlight-decoration',
              isWholeLine: false,
              inlineClassName: 'error-inline-decoration',
              stickiness: window.monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
            }
          }
        ]);
        
        // Remove the decoration after 3 seconds
        setTimeout(() => {
          window.editor.deltaDecorations(decorations, []);
        }, 3000);
        
        window.editor.focus();
      } catch (e) {
        console.error('Error jumping to position:', e);
      }
    } else {
      console.warn('Editor not available. Cannot jump to position.');
    }
  };

  // Special formatting for lexer errors to ensure line/column data is properly displayed
  const formatLexerError = (error) => {
    // Check if error has direct line/column information
    if (error.line !== undefined && error.column !== undefined) {
      // Create a unique element ID for this error
      const locationId = `lexer-err-${error.line}-${error.column}-${Math.random().toString(36).substring(2, 8)}`;
      
      // Format the message with highlighted line/column information
      let formattedMessage = error.message;
      
      // Add location information if not already present in the message
      if (!formattedMessage.includes('line') && !formattedMessage.includes('column')) {
        formattedMessage += ` <span class="error-location" id="${locationId}" data-line="${error.line}" data-column="${error.column}">(at line ${error.line}, column ${error.column})</span>`;
      } else {
        // Replace existing line/column information with highlighted version
        formattedMessage = formattedMessage.replace(
          /(at\s+)?line\s+(\d+),\s+column\s+(\d+)/i,
          `<span class="error-location" id="${locationId}" data-line="${error.line}" data-column="${error.column}">at line ${error.line}, column ${error.column}</span>`
        );
      }
      
      // Schedule the attachment of click handler
      setTimeout(() => {
        const elem = document.getElementById(locationId);
        if (elem) {
          // Remove any existing click handlers to prevent duplicates
          const newElem = elem.cloneNode(true);
          elem.parentNode.replaceChild(newElem, elem);
          
          newElem.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            jumpToErrorLocation(error.line, error.column);
          });
          
          // Add title and styling
          newElem.title = "Click to jump to this location in the editor";
          newElem.style.cursor = "pointer";
        }
      }, 10);
      
      return formattedMessage;
    }
    
    // If no direct line/column info, fall back to extracting from the message
    return formatErrorMessage(error.message);
  };

  // Check for line and column information in error messages
  const extractLineColumnInfo = (errorMessage) => {
    if (!errorMessage) return { hasLocation: false };
    
    // Multiple regex patterns to match different error message formats
    // 1. "at line X, column Y" format
    const atLineColPattern = /(?:at\s+)?line\s+(\d+),\s+column\s+(\d+)/i;
    
    // 2. "at line X" format (for errors that only mention line)
    const lineOnlyPattern = /(?:at\s+)?line\s+(\d+)(?!\s*,\s*column)/i;
    
    // 3. "Runtime Error at line X, column Y" format
    const runtimeErrorPattern = /Runtime\s+Error(?:\s+at\s+line\s+|\s*\(?line\s*|\s+\(?line\s+)(\d+)(?:,\s*(?:col(?:umn)?\s*)?(\d+))?/i;
    
    // 4. Lexer specific error pattern - captures line/column information for lexer errors
    const lexerErrorPattern = /.*?['"](.*?)['"].*?(?:line|at)\s+(\d+)(?:,\s*(?:col(?:umn)?\s*)?(\d+))?/i;
    
    let match;
    
    // Try each pattern in order
    if (match = errorMessage.match(atLineColPattern)) {
      return {
        line: parseInt(match[1], 10),
        column: parseInt(match[2], 10),
        hasLocation: true
      };
    }
    
    if (match = errorMessage.match(runtimeErrorPattern)) {
      return {
        line: parseInt(match[1], 10),
        column: match[2] ? parseInt(match[2], 10) : 1, // Default to column 1 if not specified
        hasLocation: true
      };
    }
    
    if (match = errorMessage.match(lexerErrorPattern)) {
      return {
        line: parseInt(match[2], 10),
        column: match[3] ? parseInt(match[3], 10) : 1, // Default to column 1 if not specified
        hasLocation: true,
        value: match[1] // Capture the problematic value for better context
      };
    }
    
    if (match = errorMessage.match(lineOnlyPattern)) {
      return {
        line: parseInt(match[1], 10),
        column: 1, // Default to column 1 when only line is mentioned
        hasLocation: true
      };
    }
    
    // Direct line and column properties from error object
    const directLineColMatch = /^line:(\d+),\s*column:(\d+)$/i.exec(errorMessage);
    if (directLineColMatch) {
      return {
        line: parseInt(directLineColMatch[1], 10),
        column: parseInt(directLineColMatch[2], 10),
        hasLocation: true
      };
    }
    
    return { hasLocation: false };
  };

  // Format error message to highlight line/column information and make it clickable
  const formatErrorMessage = (errorMessage) => {
    if (!errorMessage) return "Error";
    
    const { hasLocation, line, column, value } = extractLineColumnInfo(errorMessage);
    
    if (hasLocation) {
      // Create a unique ID for this error location element
      const locationId = `err-loc-${line}-${column}-${Math.random().toString(36).substring(2, 9)}`;
      
      // Pattern to match any of the line/column formats we support
      const lineColPatterns = [
        /(at\s+)?line\s+(\d+),\s+column\s+(\d+)/i,
        /(Runtime\s+Error(?:\s+at\s+line\s+|\s*\(?line\s*|\s+\(?line\s+)(\d+)(?:,\s*(?:col(?:umn)?\s*)?(\d+))?)/i,
        /(at\s+)?line\s+(\d+)(?!\s*,\s*column)/i,
        /(line:(\d+),\s*column:(\d+))/i
      ];
      
      // Check each pattern and replace the first match
      let highlighted = errorMessage;
      let matchFound = false;
      
      for (const pattern of lineColPatterns) {
        if (pattern.test(errorMessage)) {
          // Replace the matched pattern with the highlighted span
          highlighted = errorMessage.replace(
            pattern,
            `<span class="error-location" id="${locationId}" data-line="${line}" data-column="${column}">at line ${line}, column ${column}</span>`
          );
          matchFound = true;
          break;
        }
      }
      
      // If no match was found but we know there's a location, add it at the end
      if (!matchFound) {
        highlighted = `${errorMessage} <span class="error-location" id="${locationId}" data-line="${line}" data-column="${column}">(at line ${line}, column ${column})</span>`;
      }
      
      // Use a more reliable way to attach the click handler
      setTimeout(() => {
        const elem = document.getElementById(locationId);
        if (elem) {
          // Remove any existing click handlers to prevent duplicates
          const newElem = elem.cloneNode(true);
          elem.parentNode.replaceChild(newElem, elem);
          
          newElem.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            jumpToErrorLocation(line, column);
          });
          
          // Add title for better UX
          newElem.title = "Click to jump to this location in the editor";
          
          // Add visual indication that this is clickable
          newElem.style.cursor = "pointer";
        }
      }, 10);
      
      return highlighted;
    }
    
    return errorMessage;
  };

  // Helper to format each individual error
  const renderErrorItem = (error, index) => {
    // For lexical errors, use the specialized formatter that better handles line/column information
    let formattedMessage = error.type === 'lexical' && error.line !== undefined && error.column !== undefined 
      ? formatLexerError(error) 
      : (error.message && error.message !== 'Error' ? formatErrorMessage(error.message) : 'Error');
    
    return (
      <Box
        key={`${error.type}-${index}`} 
        sx={{
          mb: 1.5,
          pb: 1.5,
          borderBottom: index < errors.length - 1 ? `1px solid ${theme.palette.divider}` : 'none'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
          <Chip
            label={error.type.toUpperCase()}
            size="small"
            sx={{
              backgroundColor: getErrorBgColor(error.type),
              color: getErrorTypeColor(error.type),
              fontWeight: 'bold',
              fontSize: '0.7rem',
              height: '20px',
              mt: 0.5,
              '& .MuiChip-label': {
                px: 1
              }
            }}
          />
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="body2"
              sx={{
                fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                fontWeight: 'medium',
                mb: 0.5,
                '& .error-location': {  // Enhanced styling for error location highlights
                  fontWeight: 'bold',
                  color: theme.palette.error.main,
                  textDecoration: 'underline',
                  cursor: 'pointer',
                  padding: '2px 4px',
                  borderRadius: '3px',
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? 'rgba(244, 67, 54, 0.15)' 
                    : 'rgba(244, 67, 54, 0.08)',
                  transition: 'all 0.2s',
                  display: 'inline-block',
                  margin: '0 2px',
                  border: `1px dashed ${theme.palette.error.main}`,
                  position: 'relative',
                  '&:hover': {
                    backgroundColor: theme.palette.mode === 'dark' 
                      ? 'rgba(244, 67, 54, 0.35)' 
                      : 'rgba(244, 67, 54, 0.25)',
                    transform: 'scale(1.05)',
                    fontWeight: 800,
                    boxShadow: `0 0 4px ${theme.palette.error.main}`,
                    textDecoration: 'underline'
                  },
                  '&::before': {
                    content: '"⮞"',
                    position: 'relative',
                    marginRight: '3px',
                    fontSize: '0.85em'
                  }
                }
              }}
              dangerouslySetInnerHTML={{ __html: formattedMessage }}
            />

            {/* Keep the rest of the original code */}
            {error.unexpected && (
              <Box sx={{ pl: 1, fontSize: '0.85rem' }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: theme.palette.text.secondary,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5
                  }}
                >
                  Unexpected token: 
                  <Chip 
                    label={error.unexpected} 
                    size="small" 
                    sx={{ 
                      backgroundColor: theme.palette.mode === 'dark' ? 'rgba(244, 67, 54, 0.2)' : 'rgba(244, 67, 54, 0.1)',
                      color: theme.palette.mode === 'dark' ? '#f44336' : '#b71c1c',
                      height: '20px',
                      '& .MuiChip-label': {
                        px: 1,
                        fontSize: '0.7rem'
                      }
                    }}
                  />
                </Typography>
                {(error.literals?.length > 0 || error.keywords?.length > 0 || error.symbols?.length > 0 || error.others?.length > 0) && (
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mt: 0.5 }}>
                    Expected tokens:
                  </Typography>
                )}
                {renderExpectedCategories(error)}
              </Box>
            )}
          </Box>
        </Box>
      </Box>
    );
  };

  // Function to process terminal output with syntax highlighting
  const renderTerminalOutput = () => {
    if (!terminalOutput.trim()) {
      return (
        <Box 
          sx={{ 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            opacity: 0.7,
            color: theme.palette.text.secondary
          }}
        >
          <TerminalIcon sx={{ fontSize: '3rem', mb: 1 }} />
          <Typography variant="body2">
            No terminal output available.
          </Typography>
        </Box>
      );
    }

    return (
      <Box
        component="pre"
        sx={{
          margin: 0, 
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          fontSize: '0.8rem',
          fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
          color: theme.palette.text.primary,
          p: 0,
          m: 0
        }}
      >
        {terminalOutput.split('\n').map((line, index) => {
          let color = theme.palette.text.primary; // Default color
          
          if (line.includes('Declared variable') || line.includes('Declared global variable')) {
            color = theme.palette.mode === 'dark' ? '#4CAF50' : '#2E7D32'; // Green for variable declarations
          } else if (line.includes('Function') && line.includes('defined')) {
            color = theme.palette.mode === 'dark' ? '#2196F3' : '#1565C0'; // Blue for function definitions
          } else if (line.includes('Error:') || line.includes('error')) {
            color = theme.palette.mode === 'dark' ? '#f44336' : '#c62828'; // Red for errors
          } else if (line.includes('Execution Log')) {
            color = theme.palette.mode === 'dark' ? '#ff9800' : '#e65100'; // Orange for execution logs
          }
          
          return (
            <div key={index} style={{ color }}>
              {line}
            </div>
          );
        })}
      </Box>
    );
  };

  return (
    <Paper
      elevation={3}
      sx={{
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      {/* Header with tabs */}
      <Box
        sx={{
          backgroundColor: theme.palette.mode === 'dark' ? 'rgba(0, 0, 0, 0.2)' : 'rgba(0, 0, 0, 0.03)',
          borderBottom: `1px solid ${theme.palette.divider}`
        }}
      >
        <Tabs
          value={tabIndex}
          onChange={handleTabChange}
          variant="fullWidth"
          textColor="inherit"
          indicatorColor="primary"
          sx={{
            '.MuiTab-root': {
              minHeight: '48px',
              textTransform: 'none',
              fontWeight: tabIndex === 0 ? 'bold' : 'medium',
              fontSize: '0.9rem',
            },
          }}
        >
          <Tab 
            icon={<ErrorIcon fontSize="small" />} 
            label={hasErrors ? "Compiler Errors" : "Compilation Successful"} 
            iconPosition="start"
            sx={{ 
              color: hasErrors ? 
                theme.palette.error.main : 
                theme.palette.success.main
            }}
          />
          {debugMode && (
            <Tab 
              icon={<TerminalIcon fontSize="small" />} 
              label="Terminal Output" 
              iconPosition="start"
            />
          )}
        </Tabs>
      </Box>

      {/* Content area */}
      <Box
        ref={boxRef}
        sx={{
          height: '22vh',
          overflow: 'auto',
          padding: 2,
          backgroundColor: theme.palette.mode === 'dark' ? '#121212' : '#f8f8f8',
          color: theme.palette.text.primary,
          '&::-webkit-scrollbar': { width: '8px' },
          '&::-webkit-scrollbar-track': { background: theme.palette.mode === 'dark' ? '#333' : '#e0e0e0', borderRadius: '4px' },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: theme.palette.mode === 'dark' ? '#555' : '#bdbdbd',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': { backgroundColor: theme.palette.mode === 'dark' ? '#777' : '#9e9e9e' },
        }}
      >
        {/* Errors Tab Content */}
        {tabIndex === 0 && (
          <>
            {!hasErrors ? (
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: theme.palette.success.main
              }}>
                <CheckCircleIcon sx={{ fontSize: '3rem', mb: 1 }} />
                <Typography variant="h6" sx={{ fontWeight: 'medium' }}>
                  All checks passed!
                </Typography>
                <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mt: 1 }}>
                  Your code is looking good! No errors detected.
                </Typography>
              </Box>
            ) : (
              <Box>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexWrap: 'wrap', 
                    gap: 1, 
                    mb: 1.5 
                  }}
                >
                  {lexicalErrors.length > 0 && (
                    <Chip 
                      label={`Lexical: ${lexicalErrors.length}`} 
                      size="small" 
                      sx={{ 
                        backgroundColor: getErrorBgColor('lexical'),
                        color: getErrorTypeColor('lexical'),
                        height: '24px'
                      }} 
                    />
                  )}
                  {syntaxErrors.length > 0 && (
                    <Chip 
                      label={`Syntax: ${syntaxErrors.length}`} 
                      size="small" 
                      sx={{ 
                        backgroundColor: getErrorBgColor('syntax'),
                        color: getErrorTypeColor('syntax'),
                        height: '24px'
                      }} 
                    />
                  )}
                  {semanticErrors.length > 0 && (
                    <Chip 
                      label={`Semantic: ${semanticErrors.length}`} 
                      size="small" 
                      sx={{ 
                        backgroundColor: getErrorBgColor('semantic'),
                        color: getErrorTypeColor('semantic'),
                        height: '24px'
                      }} 
                    />
                  )}
                </Box>
                {errors.map((error, index) => {
                  return renderErrorItem(error, index);
                })}
              </Box>
            )}
          </>
        )}

        {/* Terminal Output Tab Content */}
        {debugMode && tabIndex === 1 && (
          <Box 
            sx={{ 
              height: '100%',
              overflow: 'auto'
            }}
          >
            {renderTerminalOutput()}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default Errors;