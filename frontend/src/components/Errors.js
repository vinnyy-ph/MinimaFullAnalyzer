import React, { useRef, useEffect, useState } from 'react';
import { Alert, AlertTitle, Box, Typography, Tabs, Tab, useTheme } from '@mui/material';

const Errors = ({ errors }) => {
  const theme = useTheme();
  const boxRef = useRef(null);
  const [tabIndex, setTabIndex] = useState(0);

  useEffect(() => {
    if (boxRef.current) {
      boxRef.current.scrollTop = 0;
    }
  }, [errors, tabIndex]);

  const lexicalErrors = errors.filter((error) => error.type === 'lexical');
  const syntaxErrors = errors.filter((error) => error.type === 'syntax');
  const semanticErrors = errors.filter((error) => error.type === 'semantic');

  const handleTabChange = (event, newIndex) => {
    setTabIndex(newIndex);
  };

  const currentErrors =
    tabIndex === 0 ? lexicalErrors : tabIndex === 1 ? syntaxErrors : semanticErrors;
  const hasErrors = currentErrors.length > 0;

  const arrowColor = hasErrors ? '#ff5555' : '#66ff66';
  const alertTitleColor = hasErrors ? '#ff5555' : '#66ff66';
  const secondaryTextColor = hasErrors ? '#ffcccc' : '#ccffcc';

  // Only render expected token categories if they exist separately.
  // Otherwise, we rely on the preformatted raw message.
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
      </Tabs>

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
            {currentErrors.map((error, index) => {
              // For syntax errors, prefer the rawMessage to preserve formatting.
              const formattedMessage = error.message || 'Error';       
              return (
                <li key={index} style={{ marginBottom: '0.5rem' }}>
                  <pre
                    style={{
                      whiteSpace: 'pre-wrap',
                      fontFamily:
                        'Menlo, Monaco, Consolas, "Courier New", monospace',
                      margin: 0,
                    }}
                  >
                    <Typography variant="body1" component="span">
                      <span style={{ color: arrowColor, marginRight: '8px' }}>➜</span>
                      {formattedMessage}
                    </Typography>
                    <Typography
                      variant="caption"
                      component="div"
                      sx={{ marginLeft: '16px', color: secondaryTextColor }}
                    >
                    </Typography>
                  </pre>
                  {error.unexpected && (
                    <Typography
                      variant="body2"
                      sx={{
                        marginLeft: '16px',
                        fontSize: '1rem',
                        color: secondaryTextColor,
                      }}
                    >
                      <span style={{ color: arrowColor, marginRight: '8px' }}>•</span>
                      Unexpected token: {error.unexpected} <br />
                      <span style={{ color: arrowColor, marginRight: '8px' }}>•</span>
                      Expected tokens: <br />
                      {renderExpectedCategories(error)}
                    
                    </Typography>
                  )}
                </li>
              );
            })}
          </ul>
        ) : (
          <Typography variant="body2" sx={{ color: secondaryTextColor }}>
            No errors detected in this category.
          </Typography>
        )}
      </Alert>
    </Box>
  );
};

export default Errors;