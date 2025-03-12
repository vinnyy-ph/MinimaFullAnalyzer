import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemText,
  Collapse,
} from '@mui/material';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';

const Sidebar = ({ open, toggleDrawer }) => {
  const [developersOpen, setDevelopersOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);

  const handleDevelopersClick = () => {
    setDevelopersOpen(!developersOpen);
  };

  const handleAboutClick = () => {
    setAboutOpen(!aboutOpen);
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
        <ListItem button onClick={handleDevelopersClick}>
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