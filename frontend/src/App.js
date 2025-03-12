// src/App.js

import React, { useState } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { darkTheme } from './theme';
import lightTheme from './themeLight';
import Sidebar from './components/Sidebar';
import Analyzer from './components/Analyzer';
import { Box } from '@mui/material';

const App = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [themeMode, setThemeMode] = useState('dark');

  const toggleDrawer = () => {
    setSidebarOpen(!sidebarOpen);
  };
  const toggleTheme = () => {
    setThemeMode((prevMode) => (prevMode === 'dark' ? 'light' : 'dark'));
  };

  return (
    <ThemeProvider theme={themeMode === 'dark' ? darkTheme : lightTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex' }}>
        <Sidebar open={sidebarOpen} toggleDrawer={toggleDrawer} />
        <Box component="main" sx={{ flexGrow: 1, padding: 0 }}>
          <Analyzer 
            toggleSidebar={toggleDrawer} 
            themeMode={themeMode}     
            toggleTheme={toggleTheme} 
          />
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default App;