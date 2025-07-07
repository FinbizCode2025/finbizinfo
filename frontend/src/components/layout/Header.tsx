import { FileSpreadsheet, Settings, LogOut, User, Moon, Sun, MessageCircle } from 'lucide-react'; // Add MessageCircle
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth';
import React, { useState } from 'react';

export default function Header() {
  const { logout, token } = useAuth();
  const navigate = useNavigate();
  const [darkMode, setDarkMode] = useState<boolean>(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleDarkMode = () => {
    setDarkMode((prev) => !prev);
    if (!darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileSpreadsheet className="h-8 w-8" />
            <h1 className="text-2xl font-semibold">
              Financial Analysis Suite
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <button
              className="p-2 rounded-lg hover:bg-blue-500 transition-colors flex items-center"
              title="Toggle Dark Mode"
              onClick={toggleDarkMode}
            >
              {darkMode ? <Sun className="h-6 w-6" /> : <Moon className="h-6 w-6" />}
            </button>
            <Link
              to="/profile"
              className="p-2 rounded-lg hover:bg-blue-500 transition-colors flex items-center"
              title="View Profile"
            >
              <User className="h-6 w-6 mr-1" />
              <span className="hidden sm:inline">Profile</span>
            </Link>
            <Link
              to="/feedback"
              className="p-2 rounded-lg hover:bg-blue-500 transition-colors flex items-center"
              title="Feedback"
            >
              <MessageCircle className="h-6 w-6 mr-1" />
              <span className="hidden sm:inline">Feedback</span>
            </Link>
            <button className="p-2 rounded-lg hover:bg-blue-500 transition-colors">
              <Settings className="h-6 w-6" />
            </button>
            {token && (
              <button
                className="p-2 rounded-lg hover:bg-blue-500 transition-colors flex items-center"
                title="Logout"
                onClick={handleLogout}
              >
                <LogOut className="h-6 w-6 mr-1" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}