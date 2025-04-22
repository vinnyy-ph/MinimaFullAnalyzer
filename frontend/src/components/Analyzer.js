import React, { useState, useEffect } from 'react';
import CodeEditor from './Editor';
import Buttons from './Buttons';
import OutputTable from './OutputTable';
import Errors from './Errors';
import CodeOutput from './CodeOutput';
import axios from 'axios';
import logo from '../assets/logomnm.png'; 
import { 
  Grid, 
  Box, 
  Typography, 
  IconButton, 
  useTheme, 
  Tabs, 
  Tab, 
  CircularProgress,
  Paper,
  TextField,
  InputAdornment,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import TableChartIcon from '@mui/icons-material/TableChart';
import CodeIcon from '@mui/icons-material/Code';
import OutputIcon from '@mui/icons-material/Output';

const Analyzer = ({ toggleSidebar, themeMode, toggleTheme }) => {
  const [code, setCode] = useState('');
  const [tokens, setTokens] = useState([]);
  const [errors, setErrors] = useState([]);
  const [terminalOutput, setTerminalOutput] = useState(''); 
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [fileName, setFileName] = useState('');
  const [programOutput, setProgramOutput] = useState('');
  const [tacCode, setTacCode] = useState('');
  const [executionError, setExecutionError] = useState('');
  const [rightPanelTab, setRightPanelTab] = useState(0);
  const [waitingForInput, setWaitingForInput] = useState(false);
  const [inputPrompt, setInputPrompt] = useState('');
  const [executionId, setExecutionId] = useState(null);
  const [userInput, setUserInput] = useState('');
  const [inputDialogOpen, setInputDialogOpen] = useState(false);

  const theme = useTheme();

  // Add this effect to ensure the dialog opens when input is requested
  useEffect(() => {
    if (waitingForInput) {
      setInputDialogOpen(true);
    }
  }, [waitingForInput]);

  const handleTabChange = (event, newValue) => {
    setRightPanelTab(newValue);
  };

  const handleAnalyze = () => {
    setLoading(true);
    axios.post('http://localhost:5000/analyzeFull', { code })
    .then((response) => {
      const data = response.data;
      setTokens(data.tokens);
  
      const formattedLexicalErrors = data.lexicalErrors.map(error => ({
        ...error,
        type: 'lexical'
      }));
  
      const formattedSyntaxErrors = data.syntaxErrors.map(error => ({
        ...error,
        type: 'syntax'
      }));
      
      const formattedSemanticErrors = data.semanticErrors.map(error => ({
        ...error,
        type: 'semantic'
      }));
  
      setErrors([
        ...formattedLexicalErrors,
        ...formattedSyntaxErrors,
        ...formattedSemanticErrors
      ]);
  
      // Store terminal output from response
      setTerminalOutput(data.terminalOutput || '');
      setLoading(false);
    })
    .catch((error) => {
      console.error('Unexpected error', error);
      setLoading(false);
    });
  };
  
  const handleExecute = () => {
    setExecuting(true);
    setProgramOutput('');
    setTacCode('');
    setExecutionError('');
    setWaitingForInput(false);
    setInputPrompt('');
    setExecutionId(null);
    
    // Switch to the Program Output tab when executing
    setRightPanelTab(1);
    
    axios.post('http://localhost:5000/executeCode', { code })
      .then((response) => {
        const data = response.data;
        console.log("Execute response:", data);
        console.log("Waiting for input?", data.waitingForInput);
        console.log("Input prompt:", data.inputPrompt);
        
        if (data.success) {
          setProgramOutput(data.output || 'Program executed successfully with no output.');
          setTacCode(data.formattedTAC || '');
          setExecutionError('');
          
          // Check for waiting input
          if (data.waitingForInput) {
            console.log("Waiting for input with prompt:", data.inputPrompt);
            setWaitingForInput(true);
            setInputPrompt(data.inputPrompt);
            setExecutionId(data.executionId);
            setInputDialogOpen(true);  // Open the dialog when input is requested
          }
        } else {
          setProgramOutput('');
          setTacCode(data.formattedTAC || '');
          setExecutionError(data.error || 'An unknown error occurred');
        }
        
        // Show the terminal output
        if (data.terminalOutput) {
          setTerminalOutput((prev) => prev + '\n--- Execution Log ---\n' + data.terminalOutput);
        }
        
        setExecuting(false);
      })
      .catch((error) => {
        console.error('Error executing code:', error);
        setExecutionError('Failed to connect to the server: ' + error.message);
        setExecuting(false);
      });
  };
 
  // Add this function to handle input submission
  const handleInputSubmit = (userInput) => {
    if (!executionId) return;
    
    setExecuting(true);
    
    // Add the input to the program output
    setProgramOutput((prev) => `${prev}\n${inputPrompt} ${userInput}`);
    
    console.log(`Submitting input: '${userInput}' for execution ${executionId}`);
    
    // Send the input back to the server
    axios.post('http://localhost:5000/executeCode', {
      code, // Send the code again for reference
      executionId,
      userInput
    })
    .then((response) => {
      const data = response.data;
      console.log("Input response:", data); // Debug log
      
      if (data.success) {
        // Append new output if there is any
        if (data.output && data.output.trim()) {
          setProgramOutput((prev) => `${prev}\n${data.output}`);
        }
        
        // Update TAC code
        if (data.formattedTAC) {
          setTacCode(data.formattedTAC);
        }
        
        setExecutionError('');
        
        // Check if execution is still waiting for more input
        if (data.waitingForInput) {
          setWaitingForInput(true);
          setInputPrompt(data.inputPrompt);
          setExecutionId(data.executionId);
          setInputDialogOpen(true); // Open the dialog again if more input is needed
        } else {
          setWaitingForInput(false);
          setInputPrompt('');
          setExecutionId(null);
        }
      } else {
        setExecutionError(data.error || 'An unknown error occurred');
        setWaitingForInput(false);
        setInputPrompt('');
        setExecutionId(null);
      }
      
      // Show the terminal output
      if (data.terminalOutput) {
        setTerminalOutput((prev) => `${prev}\n--- Input Processing ---\n${data.terminalOutput}`);
      }
      
      setExecuting(false);
    })
    .catch((error) => {
      console.error('Error processing input:', error);
      setExecutionError('Failed to process input: ' + error.message);
      setWaitingForInput(false);
      setInputPrompt('');
      setExecutionId(null);
      setExecuting(false);
    });
  };
 
  const handleInputDialogSubmit = () => {
    // Use the existing handleInputSubmit with the current userInput
    handleInputSubmit(userInput);
    
    // Close the dialog
    setInputDialogOpen(false);
    
    // Clear the input field for next time
    setUserInput('');
  };
  
  const handleClear = () => {
    setCode('');
    setTokens([]);
    setErrors([]);
    setTerminalOutput('');
    setProgramOutput('');
    setTacCode('');
    setExecutionError('');
  };

  const handleLoadFile = (file) => {
    setLoading(true);
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const fileContent = event.target.result;
      setCode(fileContent);
      setLoading(false);
    };
    reader.onerror = (error) => {
      console.error('Error reading file:', error);
      alert('An error occurred while reading the file.');
      setLoading(false);
    };
    reader.readAsText(file);
  };

  const handleSaveFile = async () => {
    if (!code) {
      alert('There is no code to save.');
      return;
    }
    if ('showSaveFilePicker' in window) {
      try {
        const options = {
          suggestedName: fileName ? fileName : 'code.mnm',
          types: [
            {
              description: 'Minima Files',
              accept: { 'text/plain': ['.mnm'] },
            },
          ],
        };
        const handle = await window.showSaveFilePicker(options);
        const writable = await handle.createWritable();
        await writable.write(code);
        await writable.close();
        alert('File saved successfully!');
      } catch (err) {
        console.error('Error saving file:', err);
        alert('An error occurred while saving the file.');
      }
    } else {
      const blob = new Blob([code], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const downloadName = fileName ? fileName : 'code.mnm';
      link.href = url;
      link.download = downloadName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  useEffect(() => {
    if (!code) {
      setTokens([]);
      setErrors([]);
      setTerminalOutput('');
      return;
    }

    const delayDebounceFn = setTimeout(() => {
      handleAnalyze();
    }, 100); 

    return () => clearTimeout(delayDebounceFn);
  }, [code]); 

  return (
    <div style={{ padding: '20px' }}>
      <Grid container spacing={2}>
        {/* Left side - Code Editor & Compiler Messages */}
        <Grid item xs={12} md={6}>
          {/* Code Editor */}
          <Box
            sx={{
              borderRadius: 2,
              background: theme.palette.background.paper,
              padding: 3,
              boxShadow: 3,
              mb: 2,
            }}
          >
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 2
              }}
            >
              <IconButton 
                onClick={toggleSidebar} 
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  transition: 'transform 0.2s',
                  '&:hover': {
                    backgroundColor: 'transparent',
                    transform: 'scale(1.3)',
                  },
                }}
                disableRipple
              >
                <img
                  src={logo}
                  alt="Logo"
                  style={{
                    height: '35px',
                    marginRight: '15px',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                    cursor: 'pointer',
                  }}
                />
              </IconButton>
              <Typography color='text.primary' fontWeight='bold' variant="subtitle1">
                Loaded File: {fileName || 'None'}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {(loading || executing) && (
                  <CircularProgress size={24} sx={{ marginRight: 2 }} />
                )}
                <IconButton sx={{ ml: 1 }} onClick={toggleTheme} color="inherit">
                  {themeMode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
                </IconButton>
              </Box>
            </Box>
            <CodeEditor code={code} setCode={setCode} loading={loading} />
          </Box>
          
          {/* Buttons */}
          <Buttons
            onAnalyze={handleAnalyze}
            onClear={handleClear}
            onLoadFile={handleLoadFile}
            onSaveFile={handleSaveFile}
            onExecute={handleExecute}
            disableExecute={errors.length > 0}
            executing={executing}
          />
          
          {/* Unified Error Messages */}
          <Box sx={{ mt: 2 }}>
            <Errors errors={errors} terminalOutput={terminalOutput} />
          </Box>
        </Grid>

        {/* Right side - Tabbed interface */}
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              borderRadius: 2,
              background: theme.palette.background.paper,
              boxShadow: 3,
              height: '94vh',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Tabs for switching views */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={rightPanelTab} 
                onChange={handleTabChange} 
                variant="fullWidth"
                textColor="inherit"
                indicatorColor="primary"
                sx={{
                  '.MuiTab-root': {
                    minHeight: '56px',
                    textTransform: 'none',
                    fontWeight: 'medium',
                  }
                }}
              >
                <Tab 
                  icon={<TableChartIcon />} 
                  label="Lexical Token Stream" 
                  iconPosition="start"
                />
                <Tab 
                  icon={<OutputIcon />} 
                  label="Program Output" 
                  iconPosition="start"
                />
                <Tab 
                  icon={<CodeIcon />} 
                  label="IR Representation" 
                  iconPosition="start"
                />
              </Tabs>
            </Box>
            
            {/* Tab content panels */}
            <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
              {/* Lexical Token Stream Panel */}
              {rightPanelTab === 0 && (
                <Box sx={{ height: '100%', padding: 3 }}>
                  <OutputTable tokens={tokens} />
                </Box>
              )}
              
              {/* Program Output Panel */}
              {rightPanelTab === 1 && (
                <Box sx={{ height: '100%', p: 0 }}>
                  <Box
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <Box
                      sx={{
                        padding: 2,
                        overflow: 'auto',
                        flex: 1,
                        backgroundColor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f8f8f8',
                        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                        fontSize: '0.9rem',
                        color: executionError ? '#ff5555' : theme.palette.text.primary,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
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
                      }}
                    >
                      {executionError ? (
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, p: 2 }}>
                          <Typography
                            variant="subtitle1"
                            sx={{
                              color: '#ff5555',
                              fontWeight: 'bold',
                              mb: 1,
                            }}
                          >
                            Execution Error
                          </Typography>
                          <Box component="pre" sx={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                            {executionError}
                          </Box>
                        </Box>
                      ) : programOutput ? (
                        <Box sx={{ p: 2 }}>
                          <Typography
                            variant="subtitle1"
                            sx={{
                              fontWeight: 'bold',
                              mb: 1,
                              color: theme.palette.mode === 'dark' ? '#4CAF50' : '#2E7D32',
                            }}
                          >
                            Program Output
                          </Typography>
                          <Box
                            component="pre"
                            sx={{
                              margin: 0,
                              padding: 2,
                              backgroundColor: theme.palette.mode === 'dark' ? '#111111' : '#f0f0f0',
                              borderRadius: 1,
                              border: `1px solid ${theme.palette.mode === 'dark' ? '#333' : '#ddd'}`,
                              maxHeight: 'calc(100vh - 215px)',
                              overflow: 'auto',
                            }}
                          >
                            {programOutput}
                          </Box>
                          {/* Input field for get() operations */}
                          {waitingForInput && (
                            <Box 
                              sx={{ 
                                mt: 3, 
                                p: 2, 
                                backgroundColor: theme.palette.mode === 'dark' ? '#222' : '#e8e8e8',
                                borderRadius: 1,
                                border: `1px solid ${theme.palette.mode === 'dark' ? '#444' : '#ccc'}`,
                              }}
                            >
                              <Typography 
                                variant="subtitle2" 
                                sx={{ 
                                  mb: 1, 
                                  fontWeight: 'bold',
                                  color: theme.palette.mode === 'dark' ? '#4CAF50' : '#2E7D32',
                                }}
                              >
                                Input Requested
                              </Typography>
                              <Typography variant="body2" sx={{ mb: 2 }}>
                                {inputPrompt || "Enter value:"}
                              </Typography>
                              <TextField
                                fullWidth
                                variant="outlined"
                                value={userInput}
                                onChange={(e) => setUserInput(e.target.value)}
                                onKeyPress={(event) => {
                                  if (event.key === 'Enter') {
                                    handleInputSubmit(userInput);
                                    setUserInput('');
                                    event.preventDefault();
                                  }
                                }}
                                size="small"
                                InputProps={{
                                  endAdornment: (
                                    <InputAdornment position="end">
                                      <Button 
                                        variant="contained" 
                                        color="primary"
                                        size="small" 
                                        onClick={() => {
                                          handleInputSubmit(userInput);
                                          setUserInput('');
                                        }}
                                        sx={{ ml: 1 }}
                                      >
                                        Submit
                                      </Button>
                                    </InputAdornment>
                                  ),
                                }}
                                autoFocus
                              />
                            </Box>
                          )}
                          {/* Input Dialog Modal */}
                          <Dialog 
                            open={inputDialogOpen} 
                            onClose={() => {/* Do nothing to force the user to input */}}
                            fullWidth
                            maxWidth="sm"
                            TransitionProps={{
                              onEntered: () => {
                                // Focus the input field when the dialog opens
                                const inputField = document.querySelector('#user-input-field');
                                if (inputField) inputField.focus();
                              }
                            }}
                          >
                            <DialogTitle sx={{ fontWeight: 'bold' }}>Input Required</DialogTitle>
                            <DialogContent>
                              <DialogContentText sx={{ mb: 2 }}>
                                {inputPrompt || "Enter value:"}
                              </DialogContentText>
                              <TextField
                                id="user-input-field"
                                autoFocus
                                margin="dense"
                                fullWidth
                                variant="outlined"
                                value={userInput}
                                onChange={(e) => setUserInput(e.target.value)}
                                onKeyPress={(event) => {
                                  if (event.key === 'Enter') {
                                    handleInputDialogSubmit();
                                    event.preventDefault();
                                  }
                                }}
                                sx={{ mt: 1 }}
                              />
                            </DialogContent>
                            <DialogActions>
                              <Button 
                                onClick={handleInputDialogSubmit}
                                variant="contained" 
                                color="primary"
                              >
                                Submit
                              </Button>
                            </DialogActions>
                          </Dialog>
                        </Box>
                      ) : (
                        <Box
                          sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            opacity: 0.6,
                            color: theme.palette.text.secondary,
                          }}
                        >
                          <OutputIcon sx={{ fontSize: '4rem', mb: 2 }} />
                          <Typography variant="h6" sx={{ mb: 1 }}>
                            No Output Available
                          </Typography>
                          <Typography variant="body2">
                            Click the Execute button to run your code and see the output here.
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </Box>
                </Box>
              )}
              
              {/* IR Representation Panel */}
              {rightPanelTab === 2 && (
                <Box sx={{ height: '100%', p: 0 }}>
                  <Box
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <Box
                      sx={{
                        padding: 2,
                        overflow: 'auto',
                        flex: 1,
                        backgroundColor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f8f8f8',
                        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                        fontSize: '0.85rem',
                        color: theme.palette.text.primary,
                        whiteSpace: 'pre-wrap',
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
                      }}
                    >
                      {tacCode ? (
                        <Box sx={{ p: 2 }}>
                          <Typography
                            variant="subtitle1"
                            sx={{
                              fontWeight: 'bold',
                              mb: 1,
                              color: theme.palette.primary.main,
                            }}
                          >
                            Three Address Code (TAC) - Intermediate Representation
                          </Typography>
                          <Box
                            component="pre"
                            sx={{
                              margin: 0,
                              padding: 2,
                              backgroundColor: theme.palette.mode === 'dark' ? '#111111' : '#f0f0f0',
                              borderRadius: 1,
                              border: `1px solid ${theme.palette.mode === 'dark' ? '#333' : '#ddd'}`,
                              maxHeight: 'calc(100vh - 215px)',
                              overflow: 'auto',
                            }}
                          >
                            {tacCode}
                          </Box>
                        </Box>
                      ) : (
                        <Box
                          sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            opacity: 0.6,
                            color: theme.palette.text.secondary,
                          }}
                        >
                          <CodeIcon sx={{ fontSize: '4rem', mb: 2 }} />
                          <Typography variant="h6" sx={{ mb: 1 }}>
                            No IR Code Available
                          </Typography>
                          <Typography variant="body2">
                            Click the Execute button to generate the Three Address Code representation.
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </Box>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </div>
  );
};

export default Analyzer;