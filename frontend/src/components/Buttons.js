import React, { useRef } from 'react';
import { Box, Button, Tooltip } from '@mui/material';
import ClearIcon from '@mui/icons-material/Clear';
import LoadIcon from '@mui/icons-material/FolderOpen';
import SaveIcon from '@mui/icons-material/Save'; 
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

const Buttons = ({ onAnalyze, onClear, onLoadFile, onSaveFile, onExecute, disableExecute, executing }) => {
  const fileInputRef = useRef(null);

  const handleLoadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      onLoadFile(file);
    }
    event.target.value = null;
  };

  return (
    <Box sx={{ marginTop: 3, display: 'flex', gap: 2, paddingX: 1 }}>
      <Button
        variant="contained"
        color="buttonClear"
        startIcon={<ClearIcon />}
        onClick={onClear}
        fullWidth
        sx={{ 
          fontWeight: 700, 
          fontSize: '0.9rem',
          letterSpacing: '0.5px',
          color: 'buttonClear.contrastText',
          backgroundColor: 'buttonClear.main',
          '&:hover': {
            backgroundColor: 'buttonClear.dark',
          },
        }}
      >
        Clear
      </Button>
      <Button
        variant="contained"
        color="buttonLoad"
        startIcon={<LoadIcon />}
        onClick={handleLoadClick}
        fullWidth
        sx={{ 
          fontWeight: 700, 
          fontSize: '0.9rem',
          letterSpacing: '0.5px',
          color: 'buttonLoad.contrastText',
          backgroundColor: 'buttonLoad.main',
          '&:hover': {
            backgroundColor: 'buttonLoad.dark',
          },
        }}
      >
        Load File
      </Button>
      <Button
        variant="contained"
        color="buttonSave"
        startIcon={<SaveIcon />}
        onClick={onSaveFile}
        fullWidth
        sx={{ 
          fontWeight: 700, 
          fontSize: '0.9rem',
          letterSpacing: '0.5px',
          color: 'buttonSave.contrastText',
          backgroundColor: 'buttonSave.main',
          '&:hover': {
            backgroundColor: 'buttonSave.dark',
          },
        }}
      >
        Save File
      </Button>
      <Tooltip 
        title={disableExecute ? "Fix code errors before executing" : ""}
        placement="top"
        arrow
        disableHoverListener={!disableExecute}
        enterDelay={500}
      >
        <span style={{ width: '100%' }}> {/* Wrapper needed for disabled button tooltip */}
          <Button
            variant="contained"
            color="success"
            startIcon={<PlayArrowIcon />}
            onClick={onExecute}
            disabled={disableExecute || executing}
            fullWidth
            sx={{ 
              fontWeight: 700, 
              fontSize: '0.9rem',
              letterSpacing: '0.5px',
              color: 'white',
              backgroundColor: executing ? '#a5d6a7' : disableExecute ? '#ff5252' : '#4caf50',
              '&:hover': {
                backgroundColor: executing ? '#a5d6a7' : disableExecute ? '#ff1744' : '#388e3c',
              },
              '&.Mui-disabled': {
                color: 'rgba(255, 255, 255, 0.8)',
                backgroundColor: disableExecute ? 'rgba(255, 82, 82, 0.7)' : 'rgba(165, 214, 167, 0.8)',
                opacity: 0.85,
                filter: 'grayscale(20%)',
              }
            }}
          >
            {executing ? 'Executing...' : 'Execute'}
          </Button>
        </span>
      </Tooltip>
      <input
        type="file"
        accept=".mnm"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
    </Box>
  );
};

export default Buttons;