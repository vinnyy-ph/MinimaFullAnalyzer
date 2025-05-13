import React from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  Box, 
  Typography, 
  useTheme 
} from '@mui/material';

const OutputTable = ({ tokens }) => {
  // Remove any INVALID tokens but keep ALL other tokens
  const validTokens = tokens.filter(token => token.type !== 'INVALID');
  const theme = useTheme();

  return (
    <Box sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      flex: 1,
      minHeight: 0 // ensures children can shrink and scroll
    }}>
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mb: 2,
          px: 1
        }}
      >
        <Typography variant="h5" color='text.primary' fontWeight='bold'>
          Minima Lexical Analyzer
        </Typography>
        <Box sx={{ display: 'flex', gap: '8px' }}>
          <Box sx={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: '#7ed957' }} />
          <Box sx={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: '#f44336' }} />
          <Box sx={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: '#ff9800' }} />
        </Box>
      </Box>

      {validTokens.length === 0 ? (
        <Box 
          sx={{ 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            flexGrow: 1
          }}
        >
          <Typography variant="h6" sx={{ mb: 1, color: theme.palette.text.secondary }}>
            No tokens generated yet
          </Typography>
          <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
            Write some code and the lexical analyzer will display tokens here.
          </Typography>
        </Box>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, minHeight: 0 }}>
          {/* Add debug info during development */}
          {/*<Box sx={{ mb: 2 }}>
            <Typography variant="caption">
              Debug: Found {validTokens.length} tokens to display
            </Typography>
            <pre style={{ fontSize: '10px' }}>
              {JSON.stringify(validTokens, null, 2)}
            </pre>
          </Box>*/}
          
          <TableContainer 
            component={Paper} 
            sx={{ 
              background: theme.palette.background.paper,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: 1,
              flexGrow: 1,
              minHeight: 0,
              maxHeight: '100%',   
              overflowY: 'auto',  
              '&::-webkit-scrollbar': {
                width: '8px',
                height: '8px'
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
              }
            }}
          >
            <Table 
              stickyHeader 
              aria-label='tokens table' 
              sx={{ 
                background: theme.palette.background.paper, 
                width: '100%', 
                tableLayout: 'fixed' 
              }}
            >
              <TableHead>
                <TableRow>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold', 
                      width: '80px', 
                      background: theme.palette.mode === 'dark' ? '#121212' : '#f5f5f5', 
                      color: theme.palette.text.primary 
                    }}
                  >
                    Line
                  </TableCell>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold', 
                      width: '40%', 
                      background: theme.palette.mode === 'dark' ? '#121212' : '#f5f5f5', 
                      color: theme.palette.text.primary 
                    }}
                  >
                    Lexeme
                  </TableCell>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold', 
                      width: '40%', 
                      background: theme.palette.mode === 'dark' ? '#121212' : '#f5f5f5', 
                      color: theme.palette.text.primary 
                    }}
                  >
                    Token
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {validTokens.map((token, index) => (
                  <TableRow 
                    key={index}
                    sx={{ 
                      '&:nth-of-type(odd)': {
                        backgroundColor: theme.palette.mode === 'dark' 
                          ? 'rgba(255, 255, 255, 0.05)' 
                          : 'rgba(0, 0, 0, 0.02)'
                      },
                      '&:hover': {
                        backgroundColor: theme.palette.mode === 'dark' 
                          ? 'rgba(255, 255, 255, 0.1)' 
                          : 'rgba(0, 0, 0, 0.04)'
                      }
                    }}
                  >
                    <TableCell 
                      sx={{ 
                        color: theme.palette.text.primary, 
                        py: 1,
                        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                      }}
                    >
                      {token.line}
                    </TableCell>
                    <TableCell 
                      sx={{ 
                        color: theme.palette.text.primary, 
                        wordBreak: 'break-word',
                        py: 1,
                        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                      }}
                    >
                      {token.value}
                    </TableCell>
                    <TableCell 
                      sx={{ 
                        color: getTokenColor(token.type, theme), 
                        py: 1,
                        fontWeight: 'medium',
                        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                      }}
                    >
                      {token.type}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          <Box sx={{ mt: 1, px: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Total tokens: {validTokens.length}
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
};

// Helper function to color-code different token types
function getTokenColor(tokenType, theme) {
  const colors = {
    keyword: theme.palette.mode === 'dark' ? '#ff79c6' : '#d81b60',
    identifier: theme.palette.mode === 'dark' ? '#8be9fd' : '#0288d1',
    literal: theme.palette.mode === 'dark' ? '#f1fa8c' : '#827717',
    symbol: theme.palette.mode === 'dark' ? '#ff5555' : '#d32f2f',
    whitespace: theme.palette.mode === 'dark' ? '#6272a4' : '#9e9e9e',
    default: theme.palette.text.primary
  };

  const tokenLower = tokenType.toLowerCase();
  
  if (tokenLower.includes('whitespace')) {
    return colors.whitespace;
  }
  
  if (tokenLower.includes('identifier')) {
    return colors.identifier;
  }
  
  if (
    tokenLower.includes('literal') || 
    tokenLower.includes('integerliteral') || 
    tokenLower.includes('pointliteral')
  ) {
    return colors.literal;
  }
  
  if ([
    'var','fixed','group','func','throw','show','checkif','recheck','otherwise','switch',
    'case','default','exit','next','each','repeat','do','empty','get'
  ].includes(tokenLower)) {
    return colors.keyword;
  }
  
  if (
    tokenType.length <= 3 ||
    ['PLUS','MINUS','STAR','SLASH','PERCENT','LPAREN','RPAREN','LBRACE','RBRACE','LSQB','RSQB','SEMICOLON','COMMA','COLON']
    .includes(tokenType)
  ) {
    return colors.symbol;
  }
  
  return colors.default;
}

export default OutputTable;
