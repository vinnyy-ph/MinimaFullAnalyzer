import React, { useState, useEffect } from 'react';
import CodeEditor from './Editor';
import Buttons from './Buttons';
import OutputTable from './OutputTable';
import Errors from './Errors';
import axios from 'axios';
import logo from '../assets/logomnm.png'; 
import { Grid, Box, Typography, IconButton, useTheme } from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

const Analyzer = ({ toggleSidebar, themeMode, toggleTheme }) => {
  const [code, setCode] = useState('');
  const [tokens, setTokens] = useState([]);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');
  const theme = useTheme();

  const handleAnalyze = () => {
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
    })
    .catch((error) => {
      console.error('Unexpected error', error);
    });
  
  };
  
  
  

  const handleClear = () => {
    setCode('');
    setTokens([]);
    setErrors([]);
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
        <Grid item xs={12} md={6}>
          <Box
            sx={{
              height: 'calc(65vh - 2rem)',
              borderRadius: 2,
              background: theme.palette.background.paper,
              padding: 3,
              boxShadow: 3,
            }}
          >
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 3
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
              <IconButton sx={{ ml: 1 }} onClick={toggleTheme} color="inherit">
                {themeMode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
              </IconButton>
            </Box>
            <CodeEditor code={code} setCode={setCode} loading={loading} />
          </Box>
          
          <Buttons
            onAnalyze={handleAnalyze} // optional now
            onClear={handleClear}
            onLoadFile={handleLoadFile}
            onSaveFile={handleSaveFile}
          />
          <Errors errors={errors} />
        </Grid>

        <Grid item xs={12} md={6} sx={{ height: '100%' }}>
          <Box
            sx={{
              borderRadius: 2,
              background: theme.palette.background.paper,
              padding: 3,
              boxShadow: 3,
              height: '100%',
            }}
          >
            <OutputTable tokens={tokens}/>
          </Box>
        </Grid>
      </Grid>
    </div>
  );
};

export default Analyzer;
