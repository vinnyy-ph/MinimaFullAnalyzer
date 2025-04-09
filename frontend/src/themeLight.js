// src/themeLight.js
import { createTheme } from '@mui/material/styles';

// Light Theme Configuration
const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2', // Blue
    },
    secondary: {
      main: '#dc004e', // Pink
    },
    buttonRun: {
      main: '#4caf50',    // Green color for Run button
      dark: '#388e3c',
      contrastText: '#ffffff'
    },
    background: {
      default: '#ffa2b9',
      paper: '#fe6e94',
        box: '#ffffff',
    },
    text: {
      primary: '#fffffe',
      secondary: '#424242',
    },
    buttonAnalyze: {
      main: '#fe6e94', // Blue
      contrastText: '#ffffff',
    },
    buttonClear: {
      main: '#fe6e94', // Red
      contrastText: '#ffffff',
    },
    buttonLoad: {
      main: '#fe6e94', // Orange
      contrastText: '#ffffff',
    },
    buttonSave: {
      main: '#fe6e94', // Blue
      contrastText: '#ffffff',
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

export default lightTheme;