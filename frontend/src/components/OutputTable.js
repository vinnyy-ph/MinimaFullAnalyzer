import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Box, Typography, useTheme } from '@mui/material';

const OutputTable = ({ tokens }) => {
  const validTokens = tokens.filter(token => token.type !== 'INVALID'); // Adjust the condition based on your criteria
  const theme = useTheme();

  return (
    <Box sx={{ padding: 0, margin: 0, height: '87vh', background: 'transparent' }}>
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          paddingBottom: 3 
        }}
      >
        <Typography variant="h4" color='text.primary' fontWeight='bold'>
          Minima Lexical Analyzer
        </Typography>
        <Box sx={{ display: 'flex', gap: '10px' }}>
          <Box sx={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#7ed957' }} />
          <Box sx={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#f44336' }} />
          <Box sx={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#ff9800' }} />
        </Box>
      </Box>

      <Box
        sx={{
          height: '90%',
          overflow: 'auto'
        }}
      >
        <TableContainer 
          component={Paper} 
          sx={{ 
            maxHeight: '100%', 
            background: theme.palette.background.paper,
            '&::-webkit-scrollbar': {
              width: '10px',
            },
            '&::-webkit-scrollbar-track': {
              background: theme.palette.background.default,
              borderRadius: '4px',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: theme.palette.action.hover,
              borderRadius: '10px',
              border: `2px solid ${theme.palette.background.default}`,
            },
            '&::-webkit-scrollbar-thumb:hover': {
              backgroundColor: theme.palette.action.selected,
            },
          }}
        >
          <Table 
            stickyHeader 
            aria-label='tokens table'
            sx={{ background: theme.palette.background.paper }}
          >
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold', width: '100px', background: theme.palette.background.paper, color: theme.palette.text.primary }}>Line</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '200px', background: theme.palette.background.paper, color: theme.palette.text.primary }}>Lexeme</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '150px', background: theme.palette.background.paper, color: theme.palette.text.primary }}>Token</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {validTokens.map((token, index) => (
                <TableRow key={index}>
                  <TableCell sx={{ color: theme.palette.text.primary, width: '100px' }}>{token.line}</TableCell>
                  <TableCell sx={{ color: theme.palette.text.primary, wordBreak: 'break-word', width: '200px' }}>{token.value}</TableCell>
                  <TableCell sx={{ color: theme.palette.text.primary, width: '150px' }}>{token.type}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
};

export default OutputTable;