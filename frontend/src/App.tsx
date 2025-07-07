import React, { useState } from 'react';
import { AnalysisProvider, useAnalysis } from './context/AnalysisContext';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import Hero from './components/home/Hero';
import Testimonials from './components/home/Testimonials';
import FinancialRatio from './components/FinancialRatio';
import BalanceSheetChecker from './components/BalanceSheetChecker';
import AuditorReport from './components/AuditReport';
import DirectorReport from './components/DirectorReport';
import Summary from './components/Summary';

const App: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [recentFileName, setRecentFileName] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [visibleSection, setVisibleSection] = useState<string>('');

  const { setResults } = useAnalysis();

  const handleFileUploadForMarkdown = async (file: File) => {
    if (!apiKey) {
      setErrorMessage('Please enter your API key before uploading.');
      return;
    }

    const formData = new FormData();
    formData.append('pdf', file);

    setIsUploading(true);
    setUploadProgress(0);
    setErrorMessage(null);
    setRecentFileName(file.name);

    try {
      const response = await fetch('https://finbizinfo.com/api/generate_markdown', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${apiKey}`,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to upload PDF and generate markdown.');
      }

      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        setUploadProgress(i);
      }

      const responseData = await response.json();
      setResults(prev => ({ ...prev, audit: responseData.audit }));
      setResults(prev => ({ ...prev, director: responseData.director }));
      setResults(prev => ({ ...prev, financial: responseData.financial }));

    } catch (error) {
      setErrorMessage('An error occurred while uploading the PDF. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <AnalysisProvider>
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <Hero />

        <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-2 gap-8">
            {/* API Key Section */}
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <span className="mr-2 text-blue-500 text-xl">🔑</span>
                Set Your API Key
              </h2>
              <div className="relative">
                <input
                  type="password"
                  placeholder="Enter your API key"
                  value={apiKey || ''}
                  onChange={async (e) => {
                    const newKey = e.target.value;
                    setApiKey(newKey);

                    if (newKey) {
                      try {
                        const response = await fetch('https://finbizinfo.com/api/api/set-api-key', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ api_key: newKey }),
                        });
                        if (!response.ok) {
                          const error = await response.json();
                          setErrorMessage(error.error || 'Failed to set API key.');
                        } else {
                          setErrorMessage(null);
                        }
                      } catch {
                        setErrorMessage('Failed to connect to backend to set API key.');
                      }
                    }
                  }}
                  className="block w-full text-base text-gray-900 border border-blue-300 rounded-full py-3 px-5 pr-12 bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
                />
                <span className="absolute right-4 top-1/2 transform -translate-y-1/2 text-blue-400 text-lg pointer-events-none">🔒</span>
              </div>
              {apiKey && (
                <p className="text-xs text-gray-500 mt-2">
                  API key is set. (Hidden for security)
                </p>
              )}
            </div>

            {/* File Upload Section */}
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <h5 className="text-blue-900 text-center">
                📄 Upload Financial Statement along with Audit Report (PDF)
              </h5>
              <label
                htmlFor="pdf-upload"
                className={`flex flex-col items-center justify-center w-full h-32 px-4 py-3 bg-blue-50 text-blue-700 border-2 border-dashed border-blue-400 rounded-xl cursor-pointer transition-colors duration-200 hover:bg-blue-100 ${
                  isUploading ? 'opacity-60 cursor-not-allowed' : ''
                }`}
              >
                <span className="text-4xl mb-2">⬆️</span>
                <span className="font-medium">
                  {isUploading ? 'Uploading...' : 'Click or drag PDF here to upload'}
                </span>
                <input
                  id="pdf-upload"
                  type="file"
                  accept=".pdf"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileUploadForMarkdown(e.target.files[0]);
                    }
                  }}
                  disabled={isUploading}
                  className="hidden"
                />
              </label>
              {isUploading && (
                <div className="mt-4">
                  <div className="relative w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="absolute top-0 left-0 h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{uploadProgress}%</p>
                </div>
              )}
              {errorMessage && <p className="text-sm text-red-500 mt-4">{errorMessage}</p>}
              {recentFileName && (
                <div className="mt-4">
                  <p className="text-sm text-blue-700">
                    <strong>Current File:</strong> {recentFileName}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Formal Button Section */}
          <div className="flex flex-wrap justify-center gap-4 mt-10 mb-8">
            <button
              className={`px-6 py-2 rounded-full font-semibold shadow transition 
                ${visibleSection === 'ratios' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
              onClick={() => setVisibleSection('ratios')}
            >
              Financial Ratios
            </button>
            <button
              className={`px-6 py-2 rounded-full font-semibold shadow transition 
                ${visibleSection === 'balance' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
              onClick={() => setVisibleSection('balance')}
            >
              Compliance Gaps
            </button>
            <button
              className={`px-6 py-2 rounded-full font-semibold shadow transition 
                ${visibleSection === 'audit' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
              onClick={() => setVisibleSection('audit')}
            >
              Auditor's Report section
            </button>
            <button
              className={`px-6 py-2 rounded-full font-semibold shadow transition 
                ${visibleSection === 'director' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
              onClick={() => setVisibleSection('director')}
            >
              Director's Report
            </button>
            <button
              className={`px-6 py-2 rounded-full font-semibold shadow transition 
                ${visibleSection === 'summary' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
              onClick={() => setVisibleSection('summary')}
            >
              Summary
            </button>
          </div>

          <div className="grid grid-cols-1 gap-8 mt-8">
            <div
              style={{ display: visibleSection === 'ratios' ? 'block' : 'none' }}
              className="bg-white rounded-lg p-6 shadow-sm"
            >
              <h2 className="text-lg font-semibold mb-4">Financial Ratios</h2>
              <FinancialRatio recentFileName={recentFileName} />
            </div>
            <div
              style={{ display: visibleSection === 'balance' ? 'block' : 'none' }}
              className="bg-white rounded-lg p-6 shadow-sm"
            >
              <h2 className="text-lg font-semibold mb-4">Compliance Gaps</h2>
              <BalanceSheetChecker recentFileName={recentFileName} />
            </div>
            <div
              style={{ display: visibleSection === 'audit' ? 'block' : 'none' }}
              className="bg-white rounded-lg p-6 shadow-sm"
            >
              <h2 className="text-lg font-semibold mb-4">Auditor's Report</h2>
              <AuditorReport recentFileName={recentFileName} />
            </div>
            <div
              style={{ display: visibleSection === 'director' ? 'block' : 'none' }}
              className="bg-white rounded-lg p-6 shadow-sm"
            >
              <h2 className="text-lg font-semibold mb-4">Director's Report</h2>
              <DirectorReport />
            </div>
            <div
              style={{ display: visibleSection === 'summary' ? 'block' : 'none' }}
              className="bg-white rounded-lg p-6 shadow-sm"
            >
              <h2 className="text-lg font-semibold mb-4">Summary Section</h2>
              <Summary />
            </div>
            <Testimonials />
          </div>
        </main>
        <Footer />
      </div>
    </AnalysisProvider>
  );
}

export default App;