import React, { useState, useEffect, useRef } from 'react';
import CodeEditor from './Editor';
import Buttons from './Buttons';
import OutputTable from './OutputTable';
import Errors from './Errors';
import CodeOutput from './CodeOutput';
import axios from 'axios';
import logo from '../assets/logomnm.png'; 
import Sidebar from './Sidebar';
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
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Chip
} from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import TableChartIcon from '@mui/icons-material/TableChart';
import CodeIcon from '@mui/icons-material/Code';
import OutputIcon from '@mui/icons-material/Output';
import FolderIcon from '@mui/icons-material/Folder';
import HistoryIcon from '@mui/icons-material/History';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import TableViewIcon from '@mui/icons-material/TableView';
import CloseIcon from '@mui/icons-material/Close';

const Analyzer = ({ toggleSidebar: parentToggleSidebar, themeMode, toggleTheme }) => {
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
  
  // Add new state for AST and Symbol Table
  const [astDialogOpen, setAstDialogOpen] = useState(false);
  const [symbolTableDialogOpen, setSymbolTableDialogOpen] = useState(false);
  const [ast, setAst] = useState(null);
  const [astLoading, setAstLoading] = useState(false);
  const [astError, setAstError] = useState(null);
  
  // Recent files state
  const [recentFiles, setRecentFiles] = useState([]);
  const [anchorEl, setAnchorEl] = useState(null);
  const recentFilesOpen = Boolean(anchorEl);
  
  // Terminal specific refs and states
  const terminalRef = useRef(null);
  const inputRef = useRef(null);

  // Add new state for Symbol Table
  const [symbolTable, setSymbolTable] = useState(null);
  const [symbolTableLoading, setSymbolTableLoading] = useState(false);
  const [symbolTableError, setSymbolTableError] = useState(null);
  const [symbolTableTab, setSymbolTableTab] = useState(0);

  // Add debug mode state
  const [debugMode, setDebugMode] = useState(false);

  // Add state for sidebar open
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const theme = useTheme();

  // Load recent files from localStorage when component mounts
  useEffect(() => {
    const storedFiles = localStorage.getItem('minimaRecentFiles');
    if (storedFiles) {
      try {
        setRecentFiles(JSON.parse(storedFiles));
      } catch (e) {
        console.error('Error loading recent files from localStorage:', e);
        localStorage.removeItem('minimaRecentFiles');
      }
    }
  }, []);

  // Save recent files to localStorage when it changes
  useEffect(() => {
    if (recentFiles.length > 0) {
      localStorage.setItem('minimaRecentFiles', JSON.stringify(recentFiles));
    }
  }, [recentFiles]);

  const handleRecentFilesClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleRecentFilesClose = () => {
    setAnchorEl(null);
  };

  const addToRecentFiles = (filePath, fileContent) => {
    // Add or update file in recent files list
    setRecentFiles(prevFiles => {
      // Check if file already exists in the list
      const fileIndex = prevFiles.findIndex(f => f.path === filePath);
      
      // Create new file object
      const newFile = { 
        path: filePath, 
        name: filePath.split('\\').pop(), 
        lastOpened: new Date().toISOString(),
        starred: fileIndex >= 0 ? prevFiles[fileIndex].starred : false,
        content: fileContent
      };
      
      let newFiles;
      if (fileIndex >= 0) {
        // Replace existing file
        newFiles = [...prevFiles];
        newFiles[fileIndex] = newFile;
      } else {
        // Add new file at the beginning, limit to 10 recent files
        newFiles = [newFile, ...prevFiles].slice(0, 10);
      }
      
      return newFiles;
    });
  };

  const removeFromRecentFiles = (filePath) => {
    setRecentFiles(prevFiles => prevFiles.filter(file => file.path !== filePath));
  };

  const toggleStarredFile = (filePath) => {
    setRecentFiles(prevFiles => 
      prevFiles.map(file => 
        file.path === filePath 
          ? { ...file, starred: !file.starred } 
          : file
      )
    );
  };

  const clearAllRecentFiles = () => {
    if (window.confirm('Are you sure you want to clear all recent files?')) {
      setRecentFiles([]);
      localStorage.removeItem('minimaRecentFiles');
    }
  };

  const handleOpenRecentFile = (fileContent, fileName) => {
    setCode(fileContent);
    setFileName(fileName);
    handleRecentFilesClose();
  };

  // Modified handleLoadFile to update recent files
  const handleLoadFile = (file) => {
    setLoading(true);
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const fileContent = event.target.result;
      setCode(fileContent);
      setLoading(false);
      
      // Add to recent files
      if (file.path) {
        addToRecentFiles(file.path, fileContent);
      } else {
        // For browsers that don't provide file path
        addToRecentFiles(file.name, fileContent);
      }
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

  // Modified handleTabChange to allow switching between tabs 0 and 1 regardless of debug mode
  const handleTabChange = (event, newValue) => {
    // In non-debug mode, allow switching between tabs 0 (Lexical) and 1 (Program Output)
    // In debug mode, allow switching to any tab
    if (newValue <= 1 || debugMode) {
      setRightPanelTab(newValue);
    }
  };

  // Auto-scroll to bottom of terminal output when it changes
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
    
    // Focus input field when waiting for input
    if (waitingForInput && inputRef.current) {
      inputRef.current.focus();
    }
  }, [programOutput, waitingForInput]);

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
    setUserInput('');
    
    // match to the Program Output tab when executing
    setRightPanelTab(1);
    
    axios.post('http://localhost:5000/executeCode', { code })
      .then((response) => {
        const data = response.data;
        console.log("Execute response:", data);
        
        if (data.success) {
          // 1. Process and display output received in this segment *first*
          if (data.output && data.output.trim()) {
            // Since output was cleared, just set it
            setProgramOutput(data.output);
          } else if (!data.waitingForInput) {
             // Only show 'no output' message if execution finished *and* there was no output
             setProgramOutput('Program executed successfully with no output.');
          }
          // If waiting for input and output is empty, programOutput remains empty for now

          // 2. Update TAC Code
          setTacCode(data.formattedTAC || '');
          setExecutionError(''); // Clear previous errors on success

          // 3. Handle waiting state *after* processing output
          if (data.waitingForInput) {
            setWaitingForInput(true);
            setInputPrompt(data.inputPrompt);
            setExecutionId(data.executionId);
          } else {
            // Execution finished completely in this step
            setWaitingForInput(false);
            setInputPrompt('');
            setExecutionId(null);
          }
        } else {
          // Handle execution failure reported by the backend
          setProgramOutput(''); // Clear output on error
          setTacCode(data.formattedTAC || ''); // Show TAC even on error if available
          setExecutionError(data.error || 'An unknown error occurred');
          setWaitingForInput(false); // Ensure not waiting on error
          setInputPrompt('');
          setExecutionId(null);
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
        // Clear state on connection error
        setProgramOutput('');
        setTacCode('');
        setWaitingForInput(false);
        setInputPrompt('');
        setExecutionId(null);
        setExecuting(false); // Stop loading indicator
      });
  };
 
  // Handle input submission
  const handleInputSubmit = () => {
    if (!executionId || executing) return; // Prevent multiple submissions

    setExecuting(true); // Indicate processing
    
    // Temporarily display the submitted input immediately for better UX
    // Append the prompt and the user's input to the output
    const submittedText = `${inputPrompt} ${userInput}`;
    setProgramOutput((prev) => (prev ? `${prev}\n${submittedText}` : submittedText));
    
    console.log(`Submitting input: '${userInput}' for execution ${executionId}`);
    
    // Send the input back to the server
    axios.post('http://localhost:5000/executeCode', {
      // Send code again if backend needs it for context, otherwise remove
      // code,
      executionId,
      userInput
    })
    .then((response) => {
      const data = response.data;
      console.log("Input response:", data); // Debug log
      
      if (data.success) {
        // 1. Append new output received in this segment *after* the input
        if (data.output && data.output.trim()) {
          // Append with a newline separator
          setProgramOutput((prev) => `${prev}\n${data.output}`);
        }
        
        // 2. Update TAC code if provided
        if (data.formattedTAC) {
          setTacCode(data.formattedTAC);
        }
        
        setExecutionError(''); // Clear previous errors on success
        
        // 3. Check if execution is still waiting for more input *after* processing output
        if (data.waitingForInput) {
          setWaitingForInput(true);
          setInputPrompt(data.inputPrompt);
          setExecutionId(data.executionId); // Update execution ID if necessary (though likely same unless backend changes it)
        } else {
          // Execution finished completely after this input
          setWaitingForInput(false);
          setInputPrompt('');
          setExecutionId(null);
        }
      } else {
        // Handle execution failure reported by the backend after input
        // Output might have been partially updated before error, decide if clear needed
        setExecutionError(data.error || 'An unknown error occurred');
        setWaitingForInput(false); // Ensure not waiting on error
        setInputPrompt('');
        setExecutionId(null);
        // Optionally update TAC if provided even on error
        if (data.formattedTAC) {
          setTacCode(data.formattedTAC);
        }
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
      // Reset state on connection error
      setWaitingForInput(false);
      setInputPrompt('');
      setExecutionId(null);
      setExecuting(false); // Stop loading indicator
    });
    
    // Reset input field after submission
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
    setWaitingForInput(false);
    setInputPrompt('');
    setExecutionId(null);
    setUserInput('');
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

  // Handle Enter key press in the input field
  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && waitingForInput) {
      handleInputSubmit();
      event.preventDefault();
    }
  };

  // Organize recent files with starred ones first
  const sortedRecentFiles = [...recentFiles].sort((a, b) => {
    if (a.starred && !b.starred) return -1;
    if (!a.starred && b.starred) return 1;
    return new Date(b.lastOpened) - new Date(a.lastOpened);
  });

  // Function to fetch and display the AST
  const handleShowAst = () => {
    setAstLoading(true);
    setAstError(null);
    
    axios.post('http://localhost:5000/getAST', { code })
      .then((response) => {
        const data = response.data;
        if (data.success) {
          setAst(data.ast);
          setAstDialogOpen(true);
        } else {
          setAstError(data.error || 'Failed to generate AST');
        }
        setAstLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching AST:', error);
        setAstError('Error connecting to server: ' + error.message);
        setAstLoading(false);
      });
  };
  
  // Function to fetch and display the Symbol Table
  const handleShowSymbolTable = () => {
    setSymbolTableLoading(true);
    setSymbolTableError(null);
    
    axios.post('http://localhost:5000/getSymbolTable', { code })
      .then((response) => {
        const data = response.data;
        if (data.success) {
          setSymbolTable(data.symbols);
          setSymbolTableDialogOpen(true);
        } else {
          setSymbolTableError(data.error || 'Failed to generate symbol table');
        }
        setSymbolTableLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching symbol table:', error);
        setSymbolTableError('Error connecting to server: ' + error.message);
        setSymbolTableLoading(false);
      });
  };
  
  // Helper function to render the AST tree (recursive)
  const renderAstNode = (node, index = 0) => {
    if (!node) return null;
    
    return (
      <Box key={index} sx={{ ml: 3 }}>
        <Typography 
          component="div" 
          sx={{ 
            fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
            fontSize: '0.85rem',
            color: theme.palette.mode === 'dark' ? '#9cdcfe' : '#0000ff',
            fontWeight: node.children ? 'bold' : 'normal',
            mt: 0.5
          }}
        >
          {node.name}
        </Typography>
        {node.children && node.children.map((child, idx) => renderAstNode(child, `${index}-${idx}`))}
      </Box>
    );
  };

  // Handle sidebar toggle
  const handleToggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
    // Also call the parent toggle if it exists
    if (parentToggleSidebar) {
      parentToggleSidebar();
    }
  };

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
                onClick={handleToggleSidebar} 
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
              
              {/* File name display and recent files button */}
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography color='text.primary' fontWeight='bold' variant="subtitle1">
                  {fileName ? `File: ${fileName}` : 'No File Loaded'}
                </Typography>
                <Tooltip title="Recent Files">
                  <IconButton 
                    onClick={handleRecentFilesClick}
                    color="primary"
                    size="small"
                    sx={{ ml: 1 }}
                  >
                    <ExpandMoreIcon />
                  </IconButton>
                </Tooltip>
                
                {/* Recent Files Menu */}
                <Menu
                  anchorEl={anchorEl}
                  open={recentFilesOpen}
                  onClose={handleRecentFilesClose}
                  PaperProps={{
                    sx: {
                      maxHeight: 300,
                      width: 320,
                      overflow: 'auto'
                    }
                  }}
                >
                  <Box sx={{ px: 2, py: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="subtitle2" fontWeight="bold">
                      <HistoryIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                      Recent Files
                    </Typography>
                    {recentFiles.length > 0 && (
                      <Tooltip title="Clear All">
                        <IconButton size="small" onClick={clearAllRecentFiles}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                  <Divider />
                  
                  {sortedRecentFiles.length > 0 ? (
                    sortedRecentFiles.map((file, index) => (
                      <MenuItem 
                        key={index} 
                        sx={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          paddingRight: 1
                        }}
                        onClick={() => handleOpenRecentFile(file.content, file.name)}
                      >
                        <ListItemIcon>
                          <FolderIcon fontSize="small" color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={file.name} 
                          secondary={new Date(file.lastOpened).toLocaleDateString()}
                          primaryTypographyProps={{
                            sx: { 
                              maxWidth: 180,
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              display: 'block'
                            }
                          }}
                        />
                        <Box>
                          <Tooltip title={file.starred ? "Unstar" : "Star"}>
                            <IconButton 
                              size="small" 
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleStarredFile(file.path);
                              }}
                            >
                              {file.starred ? <StarIcon fontSize="small" color="warning" /> : <StarBorderIcon fontSize="small" />}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Remove">
                            <IconButton 
                              size="small" 
                              onClick={(e) => {
                                e.stopPropagation();
                                removeFromRecentFiles(file.path);
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </MenuItem>
                    ))
                  ) : (
                    <MenuItem disabled>
                      <ListItemText primary="No recent files" />
                    </MenuItem>
                  )}
                </Menu>
              </Box>
              
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
            <Errors errors={errors} terminalOutput={terminalOutput} debugMode={debugMode} />
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
            {/* Tabs for matching views */}
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
                {debugMode && (
                  <Tab 
                    icon={<CodeIcon />} 
                    label="IR Representation" 
                    iconPosition="start"
                  />
                )}
              </Tabs>
            </Box>
            
            {/* Tab content panels */}
            <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
              {/* Lexical Token Stream Panel */}
              {rightPanelTab === 0 && (
                <Box sx={{ height: '100%', padding: 3 }}>
                  <OutputTable tokens={tokens} debugMode={debugMode} />
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
                    {/* Terminal window container */}
                    <Box
                      ref={terminalRef}
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
                        position: 'relative',
                        display: 'flex',
                        flexDirection: 'column',
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
                        // Display execution error if there is one
                        <Box sx={{ p: 1, color: '#ff5555' }}>
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
                      ) : programOutput || waitingForInput ? (
                        // Display program output container - terminal-like interface
                        <Box sx={{ p: 1, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
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
                          
                          {/* Terminal output area */}
                          <Box
                            sx={{
                              flex: 1,
                              backgroundColor: theme.palette.mode === 'dark' ? '#111111' : '#f0f0f0',
                              borderRadius: 1,
                              border: `1px solid ${theme.palette.mode === 'dark' ? '#333' : '#ddd'}`,
                              padding: 2,
                              overflowY: 'auto',
                              minHeight: '60px',
                              marginBottom: waitingForInput ? 1 : 0,
                              fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                              fontSize: '0.9rem',
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                              '&::-webkit-scrollbar': { width: '8px' },
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
                            {programOutput}
                            {/* Input field will appear as a natural continuation */}
                            {waitingForInput && (
                              <Box component="span" sx={{ display: 'inline', color: theme.palette.mode === 'dark' ? '#4CAF50' : '#2E7D32' }}>
                                {programOutput && !programOutput.endsWith('\n') ? '\n' : ''}
                                {inputPrompt} 
                              </Box>
                            )}
                          </Box>
                          
                          {/* Input field for user input - only shows when waiting for input */}
                          {waitingForInput && (
                            <Box 
                              sx={{ 
                                display: 'flex',
                                backgroundColor: theme.palette.mode === 'dark' ? '#111111' : '#f0f0f0',
                                borderRadius: 1,
                                border: `1px solid ${theme.palette.mode === 'dark' ? '#333' : '#ddd'}`,
                                borderTop: 'none',
                                borderTopLeftRadius: 0,
                                borderTopRightRadius: 0,
                              }}
                            >
                              <TextField
                                fullWidth
                                variant="outlined"
                                value={userInput}
                                onChange={(e) => setUserInput(e.target.value)}
                                onKeyPress={handleKeyPress}
                                inputRef={inputRef}
                                size="small"
                                autoFocus
                                placeholder="Type here..."
                                sx={{
                                  '& .MuiOutlinedInput-root': {
                                    '& fieldset': {
                                      border: 'none',
                                    },
                                    '&:hover fieldset': {
                                      border: 'none',
                                    },
                                    '&.Mui-focused fieldset': {
                                      border: 'none',
                                    },
                                    fontSize: '0.9rem',
                                    fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                                    backgroundColor: 'transparent',
                                    padding: '4px 8px',
                                  }
                                }}
                                InputProps={{
                                  endAdornment: (
                                    <InputAdornment position="end">
                                      <Button 
                                        variant="contained" 
                                        color="primary"
                                        size="small" 
                                        onClick={handleInputSubmit}
                                        sx={{ ml: 1 }}
                                      >
                                        Submit
                                      </Button>
                                    </InputAdornment>
                                  ),
                                }}
                              />
                            </Box>
                          )}
                          
                          {/* Only show these buttons in debug mode */}
                          {debugMode && !waitingForInput && (
                            <Box 
                              sx={{ 
                                display: 'flex', 
                                justifyContent: 'center', 
                                gap: 2,
                                mt: 3,
                                pb: 1
                              }}
                            >
                              <Button
                                variant="outlined"
                                size="small"
                                startIcon={<AccountTreeIcon />}
                                onClick={handleShowAst}
                                disabled={astLoading || errors.length > 0}
                                sx={{
                                  textTransform: 'none',
                                  borderColor: theme.palette.primary.main,
                                  color: theme.palette.primary.main,
                                  '&:hover': {
                                    backgroundColor: theme.palette.primary.main + '1A',  // 10% opacity
                                  }
                                }}
                              >
                                {astLoading ? 'Loading...' : 'Show AST'}
                              </Button>
                              
                              <Button
                                variant="outlined"
                                size="small"
                                startIcon={<TableViewIcon />}
                                onClick={handleShowSymbolTable}
                                disabled={errors.length > 0}
                                sx={{
                                  textTransform: 'none',
                                  borderColor: theme.palette.secondary.main,
                                  color: theme.palette.secondary.main,
                                  '&:hover': {
                                    backgroundColor: theme.palette.secondary.main + '1A',  // 10% opacity
                                  }
                                }}
                              >
                                Show Symbol Table
                              </Button>
                            </Box>
                          )}
                        </Box>
                      ) : (
                        // Empty state - no program output yet
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
              
              {/* IR Representation Panel - Only shown in debug mode */}
              {debugMode && rightPanelTab === 2 && (
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

      {/* AST Dialog */}
      <Dialog
        open={astDialogOpen}
        onClose={() => setAstDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: theme.palette.background.paper,
            borderRadius: 2,
            boxShadow: 24,
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: `1px solid ${theme.palette.divider}`,
          pb: 1
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AccountTreeIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
            <Typography variant="h6" component="div">
              Abstract Syntax Tree (AST)
            </Typography>
          </Box>
          <IconButton
            edge="end"
            color="inherit"
            onClick={() => setAstDialogOpen(false)}
            aria-label="close"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent 
          dividers 
          sx={{ 
            backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f5f5f5',
            p: 3
          }}
        >
          {astError ? (
            <Box sx={{ color: 'error.main', p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">Error</Typography>
              <Typography variant="body2">{astError}</Typography>
            </Box>
          ) : ast ? (
            <Box 
              sx={{ 
                padding: 2,
                borderRadius: 1,
                border: `1px solid ${theme.palette.divider}`,
                backgroundColor: theme.palette.mode === 'dark' ? '#121212' : '#ffffff',
                maxHeight: '60vh',
                overflow: 'auto',
                '&::-webkit-scrollbar': { width: '10px' },
                '&::-webkit-scrollbar-track': { 
                  background: theme.palette.mode === 'dark' ? '#2e2e2e' : '#eaeaea', 
                  borderRadius: '4px' 
                },
                '&::-webkit-scrollbar-thumb': {
                  backgroundColor: theme.palette.mode === 'dark' ? '#555' : '#aaa',
                  borderRadius: '10px',
                  border: `2px solid ${theme.palette.mode === 'dark' ? '#2e2e2e' : '#eaeaea'}`,
                }
              }}
            >
              <Typography 
                variant="subtitle1" 
                sx={{ 
                  mb: 2, 
                  fontWeight: 'bold',
                  color: theme.palette.primary.main
                }}
              >
                Parse Tree Structure
              </Typography>
              {renderAstNode(ast)}
            </Box>
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button 
            onClick={() => setAstDialogOpen(false)} 
            variant="contained"
            color="primary"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Symbol Table Dialog */}
      <Dialog
        open={symbolTableDialogOpen}
        onClose={() => setSymbolTableDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: theme.palette.background.paper,
            borderRadius: 2,
            boxShadow: 24,
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: `1px solid ${theme.palette.divider}`,
          pb: 1
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <TableViewIcon sx={{ mr: 1, color: theme.palette.secondary.main }} />
            <Typography variant="h6" component="div">
              Symbol Table
            </Typography>
          </Box>
          <IconButton
            edge="end"
            color="inherit"
            onClick={() => setSymbolTableDialogOpen(false)}
            aria-label="close"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent 
          dividers 
          sx={{ 
            backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#f5f5f5',
            p: 3
          }}
        >
          {symbolTableError ? (
            <Box sx={{ color: 'error.main', p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">Error</Typography>
              <Typography variant="body2">{symbolTableError}</Typography>
            </Box>
          ) : symbolTableLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : !symbolTable ? (
            <Box 
              sx={{ 
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                p: 4
              }}
            >
              <TableViewIcon sx={{ fontSize: '3rem', color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" sx={{ mb: 1 }}>
                No Symbol Table Data Available
              </Typography>
              <Typography variant="body2" align="center" color="text.secondary">
                Click the "Show Symbol Table" button to generate the symbol table.
              </Typography>
            </Box>
          ) : (
            <Box>
              {/* Filter Tabs */}
              <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                <Tabs 
                  value={symbolTableTab || 0} 
                  onChange={(e, newValue) => setSymbolTableTab(newValue)}
                  sx={{ mb: 1 }}
                >
                  <Tab label="All Symbols" />
                  <Tab label="Variables" />
                  <Tab label="Functions" />
                  <Tab label="Parameters" />
                </Tabs>
              </Box>
              
              {/* Symbol Table */}
              <TableContainer 
                component={Paper} 
                sx={{ 
                  maxHeight: '50vh',
                  '&::-webkit-scrollbar': { width: '10px' },
                  '&::-webkit-scrollbar-track': { 
                    background: theme.palette.mode === 'dark' ? '#2e2e2e' : '#eaeaea', 
                    borderRadius: '4px' 
                  },
                  '&::-webkit-scrollbar-thumb': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#555' : '#aaa',
                    borderRadius: '10px',
                    border: `2px solid ${theme.palette.mode === 'dark' ? '#2e2e2e' : '#eaeaea'}`,
                  }
                }}
              >
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold', backgroundColor: theme.palette.mode === 'dark' ? '#333' : '#f1f1f1' }}>Name</TableCell>
                      <TableCell sx={{ fontWeight: 'bold', backgroundColor: theme.palette.mode === 'dark' ? '#333' : '#f1f1f1' }}>Kind</TableCell>
                      <TableCell sx={{ fontWeight: 'bold', backgroundColor: theme.palette.mode === 'dark' ? '#333' : '#f1f1f1' }}>Scope</TableCell>
                      <TableCell sx={{ fontWeight: 'bold', backgroundColor: theme.palette.mode === 'dark' ? '#333' : '#f1f1f1' }}>Line:Col</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {symbolTable
                      .filter(symbol => {
                        // Remove built-in functions from all views
                        if (symbol.scope === 'builtin') return false;
                        
                        // Convert parameters into their own category
                        const symbolKind = symbol.isParameter ? 'parameter' : symbol.kind;
                        
                        // Filter based on active tab
                        if (symbolTableTab === 0) return true; // All symbols
                        if (symbolTableTab === 1) return symbolKind === 'variable'; // Variables only
                        if (symbolTableTab === 2) return symbolKind === 'function'; // User functions only
                        if (symbolTableTab === 3) return symbolKind === 'parameter'; // Parameters only
                        return true;
                      })
                      .map((symbol, index) => {
                        // Determine the actual kind to display (parameter or original kind)
                        const displayKind = symbol.isParameter ? 'parameter' : symbol.kind;
                        
                        return (
                          <TableRow 
                            key={index}
                            sx={{
                              '&:nth-of-type(odd)': {
                                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
                              },
                              '&:hover': {
                                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
                              }
                            }}
                          >
                            <TableCell>
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                                  fontWeight: displayKind === 'function' ? 'bold' : 'normal',
                                  color: displayKind === 'function' ? 
                                    (theme.palette.mode === 'dark' ? '#4fc3f7' : '#0277bd') : 
                                    theme.palette.text.primary
                                }}
                              >
                                {symbol.name}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={displayKind} 
                                size="small"
                                sx={{ 
                                  backgroundColor: 
                                    displayKind === 'function' ? 
                                      (theme.palette.mode === 'dark' ? 'rgba(33, 150, 243, 0.2)' : 'rgba(33, 150, 243, 0.1)') :
                                    displayKind === 'parameter' ?
                                      (theme.palette.mode === 'dark' ? 'rgba(255, 193, 7, 0.2)' : 'rgba(255, 193, 7, 0.1)') :
                                      (theme.palette.mode === 'dark' ? 'rgba(76, 175, 80, 0.2)' : 'rgba(76, 175, 80, 0.1)'),
                                  color: 
                                    displayKind === 'function' ? 
                                      (theme.palette.mode === 'dark' ? '#42a5f5' : '#1565c0') :
                                    displayKind === 'parameter' ?
                                      (theme.palette.mode === 'dark' ? '#ffb300' : '#ff8f00') :
                                      (theme.palette.mode === 'dark' ? '#66bb6a' : '#2e7d32'),
                                  height: '22px',
                                  '& .MuiChip-label': {
                                    fontSize: '0.7rem',
                                    px: 1
                                  }
                                }}
                              />
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={symbol.scope} 
                                size="small"
                                sx={{ 
                                  backgroundColor: 
                                    symbol.scope.startsWith('local:') ? 
                                      (theme.palette.mode === 'dark' ? 'rgba(156, 39, 176, 0.2)' : 'rgba(156, 39, 176, 0.1)') :
                                      (theme.palette.mode === 'dark' ? 'rgba(0, 137, 123, 0.2)' : 'rgba(0, 137, 123, 0.1)'),
                                  color:
                                    symbol.scope.startsWith('local:') ? 
                                      (theme.palette.mode === 'dark' ? '#ba68c8' : '#6a1b9a') :
                                      (theme.palette.mode === 'dark' ? '#26a69a' : '#00695c'),
                                  height: '22px',
                                  '& .MuiChip-label': {
                                    fontSize: '0.7rem',
                                    px: 1
                                  }
                                }}
                              />
                            </TableCell>
                            <TableCell>
                              {symbol.line && symbol.column ? (
                                <Typography 
                                  variant="body2"
                                  sx={{ 
                                    fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                                    fontSize: '0.8rem',
                                    color: theme.palette.text.secondary
                                  }}
                                >
                                  {`${symbol.line}:${symbol.column}`}
                                </Typography>
                              ) : (
                                '—'
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                  </TableBody>
                </Table>
              </TableContainer>
              
              {symbolTable.filter(symbol => symbol.scope !== 'builtin').length === 0 && (
                <Box sx={{ p: 3, textAlign: 'center' }}>
                  <Typography color="text.secondary">No symbols found in the code.</Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button 
            onClick={() => setSymbolTableDialogOpen(false)} 
            variant="contained"
            color="primary"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Update Sidebar component with correct props */}
      <Sidebar 
        open={sidebarOpen} 
        toggleDrawer={handleToggleSidebar} 
        debugMode={debugMode} 
        setDebugMode={setDebugMode} 
      />
    </div>
  );
};

export default Analyzer;