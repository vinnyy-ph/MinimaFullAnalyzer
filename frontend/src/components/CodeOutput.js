import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  useTheme, 
  Tabs, 
  Tab, 
  TextField,
  Button,
  InputAdornment
} from '@mui/material';
import CodeIcon from '@mui/icons-material/Code';
import OutputIcon from '@mui/icons-material/Output';
import ErrorIcon from '@mui/icons-material/Error';
import SendIcon from '@mui/icons-material/Send';

const CodeOutput = ({ 
  output, 
  tacCode, 
  executionError, 
  waitingForInput, 
  inputPrompt, 
  onInputSubmit 
}) => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [userInput, setUserInput] = useState('');

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleInputSubmit = () => {
    onInputSubmit(userInput);
    setUserInput('');
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleInputSubmit();
      event.preventDefault();
    }
  };

  // Check if we have an error
  const hasError = !!executionError;

  return (
    <Paper elevation={3} sx={{
      borderRadius: 2,
      background: theme.palette.background.paper,
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          textColor="inherit"
          indicatorColor="primary"
          variant="fullWidth"
        >
          <Tab 
            icon={<OutputIcon fontSize="small" />} 
            label="Program Output" 
            iconPosition="start"
            sx={{ 
              minHeight: '48px', 
              textTransform: 'none',
              fontSize: '0.875rem',
              fontWeight: 'medium'
            }}
          />
          <Tab 
            icon={<CodeIcon fontSize="small" />} 
            label="TAC Code" 
            iconPosition="start"
            sx={{ 
              minHeight: '48px', 
              textTransform: 'none',
              fontSize: '0.875rem',
              fontWeight: 'medium'
            }}
          />
        </Tabs>
      </Box>
      
      <Box sx={{ 
        padding: 2, 
        overflow: 'auto', 
        flex: 1,
        backgroundColor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f8f8f8',
        color: theme.palette.mode === 'dark' ? '#d4d4d4' : '#333',
        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
        fontSize: '0.875rem',
        '&::-webkit-scrollbar': { width: '10px' },
        '&::-webkit-scrollbar-track': { 
          background: theme.palette.mode === 'dark' ? '#2e2e2e' : '#eaeaea', 
          borderRadius: '4px' 
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: theme.palette.mode === 'dark' ? '#555' : '#aaa',
          borderRadius: '10px',
          border: `2px solid ${theme.palette.mode === 'dark' ? '#2e2e2e' : '#eaeaea'}`,
        },
        '&::-webkit-scrollbar-thumb:hover': { 
          backgroundColor: theme.palette.mode === 'dark' ? '#777' : '#888'
        },
      }}>
        {tabValue === 0 && (
          <Box sx={{ 
            fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
            fontSize: '0.9rem',
            color: hasError ? '#ff5555' : theme.palette.text.primary,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            display: 'flex', 
            flexDirection: 'column',
            height: '100%',
          }}>
            {hasError ? (
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <ErrorIcon sx={{ color: '#ff5555', mt: 0.5 }} />
                <Box>
                  <Typography 
                    variant="subtitle2" 
                    sx={{ 
                      color: '#ff5555', 
                      fontWeight: 'bold', 
                      marginBottom: 1,
                      fontFamily: 'inherit'
                    }}
                  >
                    Execution Error
                  </Typography>
                  <Box component="pre" sx={{ margin: 0 }}>
                    {executionError}
                  </Box>
                </Box>
              </Box>
            ) : (
              <>
                <Box sx={{ flex: 1 }}>
                  {output ? (
                    <Box>
                      <Typography 
                        variant="subtitle2" 
                        sx={{ 
                          fontWeight: 'bold', 
                          marginBottom: 1,
                          fontFamily: 'inherit',
                          color: theme.palette.mode === 'dark' ? '#4CAF50' : '#2E7D32'
                        }}
                      >
                        Program Output
                      </Typography>
                      <Box 
                        component="pre" 
                        sx={{ 
                          margin: 0, 
                          padding: 1.5,
                          backgroundColor: theme.palette.mode === 'dark' ? '#111111' : '#f0f0f0',
                          borderRadius: 1,
                          border: `1px solid ${theme.palette.mode === 'dark' ? '#333' : '#ddd'}`
                        }}
                      >
                        {output}
                      </Box>
                    </Box>
                  ) : waitingForInput ? (
                    <Box>
                      <Typography 
                        variant="subtitle2" 
                        sx={{ 
                          fontWeight: 'bold', 
                          marginBottom: 1,
                          fontFamily: 'inherit',
                          color: theme.palette.mode === 'dark' ? '#4CAF50' : '#2E7D32'
                        }}
                      >
                        Program Output
                      </Typography>
                      <Box 
                        component="pre" 
                        sx={{ 
                          margin: 0, 
                          padding: 1.5,
                          backgroundColor: theme.palette.mode === 'dark' ? '#111111' : '#f0f0f0',
                          borderRadius: 1,
                          border: `1px solid ${theme.palette.mode === 'dark' ? '#333' : '#ddd'}`
                        }}
                      >
                        {/* Empty for now - will show output after input */}
                      </Box>
                    </Box>
                  ) : (
                    <Box sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      height: '100%',
                      opacity: 0.6,
                      color: theme.palette.text.secondary
                    }}>
                      <OutputIcon sx={{ fontSize: '3rem', mb: 1 }} />
                      <Typography variant="body2">
                        No output. Run your code to see results here.
                      </Typography>
                    </Box>
                  )}
                </Box>
                
                {/* Input field when waiting for input */}
                {waitingForInput && (
                  <Box 
                    sx={{ 
                      mt: 3, 
                      p: 2, 
                      backgroundColor: theme.palette.mode === 'dark' ? '#222' : '#e8e8e8',
                      borderRadius: 1,
                    }}
                  >
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        mb: 1, 
                        fontWeight: 'bold',
                        color: theme.palette.mode === 'dark' ? '#4CAF50' : '#2E7D32'
                      }}
                    >
                      Input Requested
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {inputPrompt || ""}
                    </Typography>
                    <TextField
                      fullWidth
                      variant="outlined"
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      size="small"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <Button 
                              variant="contained" 
                              size="small" 
                              onClick={handleInputSubmit}
                              sx={{ ml: 1 }}
                              startIcon={<SendIcon />}
                            >
                              Submit
                            </Button>
                          </InputAdornment>
                        ),
                      }}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          backgroundColor: theme.palette.mode === 'dark' ? '#333' : '#fff',
                        }
                      }}
                      autoFocus
                    />
                  </Box>
                )}
              </>
            )}
          </Box>
        )}
        
        {tabValue === 1 && (
          <Box sx={{ 
            fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
            fontSize: '0.85rem',
            color: theme.palette.text.primary,
            whiteSpace: 'pre-wrap',
            height: '100%'
          }}>
            {tacCode ? (
              <Box>
                <Typography 
                  variant="subtitle2" 
                  sx={{ 
                    fontWeight: 'bold', 
                    marginBottom: 1,
                    fontFamily: 'inherit',
                    color: theme.palette.primary.main
                  }}
                >
                  Three Address Code (TAC) - Intermediate Representation
                </Typography>
                <Box 
                  component="pre" 
                  sx={{ 
                    margin: 0, 
                    padding: 1.5,
                    backgroundColor: theme.palette.mode === 'dark' ? '#111111' : '#f0f0f0',
                    borderRadius: 1,
                    border: `1px solid ${theme.palette.mode === 'dark' ? '#333' : '#ddd'}`
                  }}
                >
                  {tacCode}
                </Box>
              </Box>
            ) : (
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                justifyContent: 'center',
                height: '100%',
                opacity: 0.6,
                color: theme.palette.text.secondary
              }}>
                <CodeIcon sx={{ fontSize: '3rem', mb: 1 }} />
                <Typography variant="body2">
                  No TAC code generated. Run your code to see the intermediate representation.
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default CodeOutput;