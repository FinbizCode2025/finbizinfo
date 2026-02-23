import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Failed to find the root element');

createRoot(rootElement).render(
  <React.StrictMode>
      <BrowserRouter>
        <Routes>
          <Route path="/*" element={
              <App />
          } />
        </Routes>
      </BrowserRouter>
  </React.StrictMode>
);