import React, { useRef, useEffect, useState } from 'react';
import { Alert, AlertTitle, Box, Typography, Tabs, Tab, useTheme } from '@mui/material';


const Errors = ({ errors, terminalOutput = '' }) => {
  const theme = useTheme();
  const boxRef = useRef(null);
  const [tabIndex, setTabIndex] = useState(0);

  useEffect(() => {
    if (boxRef.current) {
      boxRef.current.scrollTop = 0;
    }
  }, [errors, tabIndex, terminalOutput]);

  const lexicalErrors = errors.filter((error) => error.type === 'lexical');
  const syntaxErrors = errors.filter((error) => error.type === 'syntax');
  const semanticErrors = errors.filter((error) => error.type === 'semantic');

  const handleTabChange = (event, newIndex) => {
    setTabIndex(newIndex);
  };

  let currentErrors = [];
  let hasErrors = false;
  let isTerminalTab = false;

  if (tabIndex === 0) {
    currentErrors = lexicalErrors;
  } else if (tabIndex === 1) {
    currentErrors = syntaxErrors;
  } else if (tabIndex === 2) {
    currentErrors = semanticErrors;
  } else {
    // Terminal tab
    isTerminalTab = true;
    hasErrors = false;
  }

  if (!isTerminalTab) {
    hasErrors = currentErrors.length > 0;
  }

  // Consistent color styling for errors or success
  const errorColor = hasErrors ? '#ff5555' : '#66ff66';
  const alertTitleColor = hasErrors ? '#ff5555' : '#66ff66';
  const secondaryTextColor = hasErrors ? '#ffcccc' : '#ccffcc';

  // Render expected token categories if present
  const renderExpectedCategories = (error) => {
    const { literals, keywords, symbols, others } = error;
    if (!literals?.length && !keywords?.length && !symbols?.length && !others?.length) {
      return null;
    }

    return (
      <ul style={{ listStyleType: 'disc', paddingLeft: '20px', marginTop: '4px' }}>
        {literals?.length > 0 && (
          <li>
            <Typography variant="body2" sx={{ color: secondaryTextColor }}>
              <strong>Literals:</strong> {literals.join(' ')}
            </Typography>
          </li>
        )}
        {keywords?.length > 0 && (
          <li>
            <Typography variant="body2" sx={{ color: secondaryTextColor }}>
              <strong>Keywords:</strong> {keywords.join(' ')}
            </Typography>
          </li>
        )}
        {symbols?.length > 0 && (
          <li>
            <Typography variant="body2" sx={{ color: secondaryTextColor }}>
              <strong>Symbols:</strong> {symbols.join(' ')}
            </Typography>
          </li>
        )}
        {others?.length > 0 && (
          <li>
            <Typography variant="body2" sx={{ color: secondaryTextColor }}>
              <strong>Others:</strong> {others.join(' ')}
            </Typography>
          </li>
        )}
      </ul>
    );
  };

  // Helper to format each individual error
  const renderErrorItem = (error) => {
    let formattedMessage =
      error.message && error.message !== 'Error' ? error.message : 'Error';

    if (error.line && error.column) {
      formattedMessage += ` (Line ${error.line}, Col ${error.column})`;
    }

    return (
      <li key={formattedMessage} style={{ marginBottom: '1rem' }}>
        {/* Bullet + Main Error Message */}
        <Typography
          variant="body1"
          component="div"
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
          }}
        >
          <span style={{ color: errorColor, marginRight: '8px', marginTop: '3px' }}>•</span>
          <span>{formattedMessage}</span>
        </Typography>

        {/* Unexpected tokens / expected tokens */}
        {error.unexpected && (
          <Box sx={{ marginLeft: '24px' }}>
            <Typography variant="body2" sx={{ color: secondaryTextColor }}>
              <span style={{ color: errorColor, marginRight: '8px' }}>•</span>
              Unexpected token: {error.unexpected}
            </Typography>
            <Typography variant="body2" sx={{ color: secondaryTextColor }}>
              <span style={{ color: errorColor, marginRight: '8px' }}>•</span>
              Expected tokens:
            </Typography>
            <Box sx={{ marginLeft: '24px' }}>{renderExpectedCategories(error)}</Box>
          </Box>
        )}
      </li>
    );
  };

  // Terminal output renderer
  const renderTerminalOutput = () => {
    // Check if there are any errors before showing terminal output
    const hasAnyErrors = lexicalErrors.length > 0 || syntaxErrors.length > 0 || semanticErrors.length > 0;
    
    if (hasAnyErrors) {
      // Show error message instead of terminal output when errors exist
      let message = "Errors detected. Resolve them before seeing terminal output.";
      
      if (lexicalErrors.length > 0) {
        message = "Lexical errors detected. Resolve them before seeing terminal output.";
      } else if (syntaxErrors.length > 0) {
        message = "Syntax errors detected. Resolve them before seeing terminal output.";
      } else if (semanticErrors.length > 0) {
        message = "Semantic errors detected. Resolve them before seeing terminal output.";
      }
      
      return (
        <Typography variant="body2" sx={{ color: '#ff5555', fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace' }}>
          {message}
        </Typography>
      );
    }

    if (!terminalOutput.trim()) {
      return (
        <Typography variant="body2" sx={{ color: '#ccffcc', fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace' }}>
          No terminal output available.
        </Typography>
      );
    }

    // Process terminal lines with simple syntax highlighting
    return (
      <pre style={{ 
        margin: 0, 
        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word'
      }}>
        {terminalOutput.split('\n').map((line, index) => {
          let color = '#d4d4d4'; // Default color
          
          if (line.includes('Declared variable') || line.includes('Declared global variable')) {
            color = '#4CAF50'; // Green for variable declarations
          } else if (line.includes('Function') && line.includes('defined')) {
            color = '#2196F3'; // Blue for function definitions
          } else if (line.includes('Error:') || line.includes('error')) {
            color = '#FF5555'; // Red for errors
          }
          
          return (
            <div key={index} style={{ color }}>
              {line}
            </div>
          );
        })}
      </pre>
    );
  };

  return (
    <Box
      ref={boxRef}
      sx={{
        marginTop: 3,
        height: '21vh',
        overflow: 'auto',
        width: '100%',
        padding: 2,
        borderRadius: 2,
        backgroundColor: '#001524',
        color: '#d4d4d4',
        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
        boxShadow: 1,
        '&::-webkit-scrollbar': { width: '10px' },
        '&::-webkit-scrollbar-track': { background: '#2e2e2e', borderRadius: '4px' },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: '#555',
          borderRadius: '10px',
          border: '2px solid #2e2e2e',
        },
        '&::-webkit-scrollbar-thumb:hover': { backgroundColor: '#777' },
      }}
    >
      <Tabs
        value={tabIndex}
        onChange={handleTabChange}
        textColor="inherit"
        indicatorColor="primary"
        centered
        sx={{
          marginBottom: 2,
          '.MuiTabs-flexContainer': {
            borderBottom: '1px solid #444',
          },
          '.MuiTab-root': {
            fontWeight: 'bold',
            textTransform: 'none',
          },
        }}
      >
        <Tab label={`Lexical Errors (${lexicalErrors.length})`} />
        <Tab label={`Syntax Errors (${syntaxErrors.length})`} />
        <Tab label={`Semantic Errors (${semanticErrors.length})`} />
        <Tab label="Terminal Output" />
      </Tabs>

      {isTerminalTab ? (
        // Terminal Tab Content
        <Box sx={{ padding: 1 }}>
          {renderTerminalOutput()}
        </Box>
      ) : (
        // Error Tabs Content
        <Alert
          severity={hasErrors ? 'error' : 'success'}
          sx={{
            background: 'transparent',
            color: theme.palette.text.primary,
            width: '100%',
          }}
        >
          <AlertTitle sx={{ fontWeight: 'bold', color: alertTitleColor }}>
            {hasErrors
              ? tabIndex === 0
                ? 'Lexical Errors'
                : tabIndex === 1
                ? 'Syntax Errors'
                : 'Semantic Errors'
              : 'You understand Minima, Good Job!'}
          </AlertTitle>

          {hasErrors ? (
            <ul style={{ listStyleType: 'none', paddingLeft: 0, margin: 0 }}>
              {currentErrors.map(renderErrorItem)}
            </ul>
          ) : (
            <Typography variant="body2" sx={{ color: secondaryTextColor }}>
              {tabIndex === 2 && syntaxErrors.length > 0
                ? 'Syntax errors detected. Resolve them before semantic analysis.'
                : 'No errors detected in this category.'}
            </Typography>
          )}
        </Alert>
      )}
    </Box>
  );
};

export default Errors;