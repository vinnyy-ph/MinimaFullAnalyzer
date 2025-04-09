import React, { useRef, useEffect } from 'react';
import { Box, Typography, Paper, Divider, CircularProgress } from '@mui/material';

const ProgramOutput = ({ output, error, loading }) => {
  const outputRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom when output changes
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output, error]);

  return (
    <Paper
      elevation={3}
      sx={{
        height: '100%',
        borderRadius: 2,
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.paper'
      }}
    >
      <Box
        sx={{
          padding: '12px 16px',
          borderBottom: '1px solid',
          borderColor: 'divider',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <Typography variant="subtitle1" fontWeight="bold">
          Program Output
        </Typography>
        {loading && <CircularProgress size={24} />}
      </Box>

      <Box
        ref={outputRef}
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          padding: 2,
          fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
          fontSize: '0.9rem',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          color: error ? 'error.main' : 'text.primary',
          '&::-webkit-scrollbar': { width: '10px' },
          '&::-webkit-scrollbar-track': {
            background: theme => theme.palette.background.default,
            borderRadius: '4px'
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: theme => theme.palette.action.hover,
            borderRadius: '10px',
            border: theme => `2px solid ${theme.palette.background.default}`
          },
          '&::-webkit-scrollbar-thumb:hover': {
            backgroundColor: theme => theme.palette.action.selected
          }
        }}
      >
        {loading ? (
          <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
            Running program...
          </Typography>
        ) : error ? (
          <>
            <Typography variant="body2" color="error" fontWeight="bold">
              Execution Error:
            </Typography>
            <Box sx={{ mt: 1 }}>{error}</Box>
          </>
        ) : !output ? (
          <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
            No output yet. Click "Run Code" to execute your program.
          </Typography>
        ) : (
          output
        )}
      </Box>
    </Paper>
  );
};

export default ProgramOutput;