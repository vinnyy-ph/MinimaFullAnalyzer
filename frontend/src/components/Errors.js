import React, { useRef, useEffect, useState } from 'react';
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
  CircularProgress
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import TerminalIcon from '@mui/icons-material/Terminal';
import CodeIcon from '@mui/icons-material/Code';

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

  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
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

  // Helper to format each individual error
  const renderErrorItem = (error, index) => {
    let formattedMessage =
      error.message && error.message !== 'Error' ? error.message : 'Error';

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
                mb: 0.5
              }}
            >
              {formattedMessage}
              {error.line && error.column && (
                <Box 
                  component="span" 
                  sx={{ 
                    ml: 1, 
                    fontWeight: 'normal',
                    color: theme.palette.text.secondary,
                    fontSize: '0.8rem'
                  }}
                >
                  (Line {error.line}, Col {error.column})
                </Box>
              )}
            </Typography>

            {/* Unexpected tokens / expected tokens */}
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
          <Tab 
            icon={<TerminalIcon fontSize="small" />} 
            label="Terminal Output" 
            iconPosition="start"
          />
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
                {errors.map((error, index) => renderErrorItem(error, index))}
              </Box>
            )}
          </>
        )}

        {/* Terminal Output Tab Content */}
        {tabIndex === 1 && (
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