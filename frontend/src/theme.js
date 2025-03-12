// src/theme.js
import { createTheme } from '@mui/material/styles';

// Dark Theme Configuration
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9', // Light blue
    },
    secondary: {
      main: '#f50057', // Pink
    },
    background: {
      default: '#161b33',
      paper: '#001524',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0bec5',
    },
    buttonAnalyze: {
      main: '#001524', // Green
      contrastText: '#7ed957',
      dark: '#002b4a',

    },
    buttonClear: {
      main: '#001524', // Red
      contrastText: '#f44336',
      dark: '#002b4a',

    },
    buttonLoad: {
      main: '#001524', // Orange
      contrastText: '#ff9800',
      dark: '#002b4a',

    },
    buttonSave: {
      main: '#001524', // Blue
      contrastText: '#ffffff',
      dark: '#002b4a',
    },
  },
  typography: {
    fontFamily: 'Google Sans, Arial, sans-serif',
  },
  components: {
    // Override default MUI component styles if needed
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
        },
      },
    },
    // Add more component overrides as needed
  },
});

export { darkTheme };