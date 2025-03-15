import React, { useRef, useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  useTheme, 
  Paper, 
  IconButton, 
  TextField,
  Menu,
  MenuItem,
  Tooltip,
  Divider
} from '@mui/material';
import TerminalIcon from '@mui/icons-material/Terminal';
import ClearIcon from '@mui/icons-material/Clear';
import FilterListIcon from '@mui/icons-material/FilterList';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import SaveIcon from '@mui/icons-material/Save';

// Function to add syntax highlighting
const processOutput = (text, filterText) => {
  if (!text) return null;
  
  // Filter lines if filterText is provided
  let lines = text.split('\n');
  if (filterText) {
    const lowerFilter = filterText.toLowerCase();
    lines = lines.filter(line => line.toLowerCase().includes(lowerFilter));
  }
  
  return lines.map((line, index) => {
    // Highlight different types of messages
    if (line.includes('Declared variable') || line.includes('Declared global variable')) {
      return (
        <Box component="span" key={index} sx={{ color: '#4CAF50', display: 'block' }}>
          {line}
        </Box>
      );
    } else if (line.includes('Function') && line.includes('defined')) {
      return (
        <Box component="span" key={index} sx={{ color: '#2196F3', display: 'block' }}>
          {line}
        </Box>
      );
    } else if (line.includes('Error') || line.includes('error')) {
      return (
        <Box component="span" key={index} sx={{ color: '#FF5252', display: 'block' }}>
          {line}
        </Box>
      );
    } else if (line.includes('Warning') || line.includes('warning')) {
      return (
        <Box component="span" key={index} sx={{ color: '#FFC107', display: 'block' }}>
          {line}
        </Box>
      );
    }
    return <Box component="span" key={index} sx={{ display: 'block' }}>{line}</Box>;
  });
};

const EnhancedTerminal = ({ output }) => {
  const theme = useTheme();
  const terminalRef = useRef(null);
  const [filterText, setFilterText] = useState('');
  const [showFilter, setShowFilter] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  
  // Auto-scroll to bottom when output changes
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output, filterText]);

  const handleClearOutput = () => {
    // Emit an event to parent to clear output
    const event = new CustomEvent('clearTerminal');
    window.dispatchEvent(event);
  };

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(output);
  };

  const handleSaveToFile = () => {
    const blob = new Blob([output], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'terminal-output.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleOpenMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
  };

  const toggleFilter = () => {
    setShowFilter(!showFilter);
    if (!showFilter) {
      setFilterText('');
    }
  };
  
  return (
    <Paper 
      elevation={3}
      sx={{
        marginTop: 3,
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 16px',
          backgroundColor: theme.palette.mode === 'dark' ? '#1a1a1a' : '#e0e0e0',
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TerminalIcon sx={{ marginRight: 1, color: theme.palette.mode === 'dark' ? '#66ff66' : '#006600' }} />
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
            Terminal Output
          </Typography>
        </Box>
        
        <Box>
          <Tooltip title="Filter">
            <IconButton size="small" onClick={toggleFilter}>
              <FilterListIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Copy to clipboard">
            <IconButton size="small" onClick={handleCopyToClipboard}>
              <ContentCopyIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Clear terminal">
            <IconButton size="small" onClick={handleClearOutput}>
              <ClearIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="More options">
            <IconButton size="small" onClick={handleOpenMenu}>
              <MoreVertIcon />
            </IconButton>
          </Tooltip>
          
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleCloseMenu}
          >
            <MenuItem onClick={handleSaveToFile}>
              <SaveIcon fontSize="small" sx={{ mr: 1 }} />
              Save to file
            </MenuItem>
          </Menu>
        </Box>
      </Box>
      
      {showFilter && (
        <Box sx={{ padding: '8px 16px', backgroundColor: theme.palette.background.default }}>
          <TextField
            size="small"
            fullWidth
            placeholder="Filter output..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            variant="outlined"
            InputProps={{
              sx: { 
                fontSize: '0.875rem',
                fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
              }
            }}
          />
        </Box>
      )}
      
      <Box
        ref={terminalRef}
        sx={{
          height: '25vh',
          overflow: 'auto',
          padding: 2,
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
        }}
      >
        <Box
          component="div"
          sx={{
            margin: 0,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {output ? 
            processOutput(output, filterText) : 
            'No terminal output available. Try running some code.'}
        </Box>
      </Box>
    </Paper>
  );
};

export default EnhancedTerminal;