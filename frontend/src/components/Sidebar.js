import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemText,
  Collapse,
  Switch,
  ListItemIcon,
  Typography,
  Box,
} from '@mui/material';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import SettingsIcon from '@mui/icons-material/Settings';
import BugReportIcon from '@mui/icons-material/BugReport';
import CodeIcon from '@mui/icons-material/Code';
import GroupIcon from '@mui/icons-material/Group';
import InfoIcon from '@mui/icons-material/Info';

const Sidebar = ({ open, toggleDrawer, debugMode, setDebugMode }) => {
  const [developersOpen, setDevelopersOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const handleDevelopersClick = () => {
    setDevelopersOpen(!developersOpen);
  };

  const handleAboutClick = () => {
    setAboutOpen(!aboutOpen);
  };
  
  const handleSettingsClick = () => {
    setSettingsOpen(!settingsOpen);
  };
  
  const handleDebugModeToggle = () => {
    setDebugMode(!debugMode);
  };
  
  const developers = [
    'Bautista, Anna Kathlyn A.',
    'Fallaria, Immaculate L.',
    'Ferrer, Vincent P.',
    'Pantoja, Rhayzel S.',
    'Pineda, Miguel Ynigo T.',
    'Revaula, Alexcszis Rasec T.',
  ];

  const languageDescription = `
    Minima is a beginner-friendly programming language designed for simplicity and clarity, using a natural and intuitive syntax that resembles everyday language.
  `;

  return (
    <Drawer
      anchor="left"
      open={open}
      onClose={toggleDrawer}
      sx={{
        '& .MuiDrawer-paper': {
          backgroundColor: '#161b33',
          color: '#fff',
          fontFamily: 'Google Sans, Arial, sans-serif',
          width: 250,
        },
      }}
    >
      <List>
        <ListItem button onClick={handleSettingsClick}>
          <ListItemIcon>
            <SettingsIcon sx={{ color: '#fff' }} />
          </ListItemIcon>
          <ListItemText primary="Settings" />
          {settingsOpen ? <ExpandLess /> : <ExpandMore />}
        </ListItem>
        <Collapse in={settingsOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            <ListItem sx={{ pl: 4 }}>
              <ListItemIcon>
                <BugReportIcon sx={{ color: '#fff' }} />
              </ListItemIcon>
              <ListItemText primary="Debug Mode" />
              <Switch 
                checked={debugMode} 
                onChange={handleDebugModeToggle} 
                color="primary"
              />
            </ListItem>
            <ListItem sx={{ pl: 4 }}>
              <Box sx={{ pl: 4.5, fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)' }}>
                <Typography variant="caption">
                  Shows terminal output, token stream, AST and symbol table tools
                </Typography>
              </Box>
            </ListItem>
          </List>
        </Collapse>

        <ListItem button onClick={handleDevelopersClick}>
          <ListItemIcon>
            <GroupIcon sx={{ color: '#fff' }} />
          </ListItemIcon>
          <ListItemText primary="Developers" />
          {developersOpen ? <ExpandLess /> : <ExpandMore />}
        </ListItem>
        <Collapse in={developersOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {developers.map((dev, index) => (
              <ListItem key={index} sx={{ pl: 4 }}>
                <ListItemText primary={dev} />
              </ListItem>
            ))}
          </List>
        </Collapse>

        <ListItem button onClick={handleAboutClick}>
          <ListItemIcon>
            <InfoIcon sx={{ color: '#fff' }} />
          </ListItemIcon>
          <ListItemText primary="About the Language" />
          {aboutOpen ? <ExpandLess /> : <ExpandMore />}
        </ListItem>
        <Collapse in={aboutOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            <ListItem sx={{ pl: 4 }}>
              <ListItemText primary={languageDescription} />
            </ListItem>
          </List>
        </Collapse>
      </List>
    </Drawer>
  );
};

export default Sidebar;