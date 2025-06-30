import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Chatus from './components/chatbot/Main';
import FinancialRatio from './components/FinancialRatio';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Failed to find the root element');

createRoot(rootElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Home Route */}
        <Route path="/" element={<App />} />

        {/* Financial Ratio Route */}
        <Route path="financial_ratio" element={<FinancialRatio recentFileName={null} />} />

        {/* 404 Route */}
        <Route path="*" element={<div>404 Not Found</div>} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);