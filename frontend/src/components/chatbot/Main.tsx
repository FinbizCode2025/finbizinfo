import { useState } from 'react';
import './Main.css';
import CompanyIntro from './components/CompanyIntro.js';  // Import the company intro component
import Chatbox from './components/Chatbox.tsx';  // Import the chatbox component

function Main() {
  const [darkMode, setDarkMode] = useState(false); // State for dark mode toggle

  const toggleDarkMode = () => {
    setDarkMode(!darkMode); // Toggle dark mode state
  };

  return (
    <div className={`App ${darkMode ? 'dark' : 'light'}`}>
      {/* Dark Mode Toggle Button */}
      <button className="dark-mode-toggle" onClick={toggleDarkMode}>
        {darkMode ? '🌙' : '🌞'} {/* Moon or Sun symbol based on darkMode state */}
      </button>

      {/* Main Content (Company Intro) */}
      <CompanyIntro />

      {/* Chatbox Component */}
      <Chatbox darkMode={darkMode} />
    </div>
  );
}

export default Main;
