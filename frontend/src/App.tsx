import { useState } from 'react';
import Header from '../src/components/layout/Header';
import Footer from '../src/components/layout/Footer';
import Hero from '../src/components/home/Hero';
import Testimonials from '../src/components/home/Testimonials';
import FinancialRatio from '../src/components/FinancialRatio';
import BalanceSheetChecker from '../src/components/BalanceSheetChecker';
import AuditorReport from '../src/components/AuditReport';
import DirectorReport from '../src/components/DirectorReport';

function App() {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [recentFileName, setRecentFileName] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null); // State for API key

  // States to clear results for each section
  const [financialRatioResults, setFinancialRatioResults] = useState(null);
  const [balanceSheetResults, setBalanceSheetResults] = useState(null);
  const [auditorReportResults, setAuditorReportResults] = useState(null);
  const [directorReportResults, setDirectorReportResults] = useState(null);

  const handleFileUploadForMarkdown = async (file: File) => {
    if (!apiKey) {
      setErrorMessage('Please enter your API key before uploading.');
      return;
    }

    // Clear previous results when a new file is selected
    setFinancialRatioResults(null);
    setBalanceSheetResults(null);
    setAuditorReportResults(null);
    setDirectorReportResults(null);

    const formData = new FormData();
    formData.append('pdf', file);

    setIsUploading(true);
    setUploadProgress(0);
    setErrorMessage(null);
    setRecentFileName(file.name);

    try {
      const response = await fetch('http://82.180.145.47:5002/generate_markdown', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${apiKey}`, // Pass the API key dynamically
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to upload PDF and generate markdown.');
      }

      // Simulate progress for better UX
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        setUploadProgress(i);
      }

      console.log('Markdown file generated successfully.');
    } catch (error) {
      console.error('Error uploading PDF:', error);
      setErrorMessage('An error occurred while uploading the PDF. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <Hero />

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-2 gap-8">
          {/* API Key Section */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Set Your API Key</h2>
            <input
              type="password"
              placeholder="Enter your API key"
              value={apiKey || ''}
              onChange={(e) => setApiKey(e.target.value)}
              className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg p-2 focus:outline-none"
            />
            {apiKey && (
              <p className="text-sm text-gray-700 mt-4">
                {/* <strong>Current API Key:</strong> <span className="italic">Hidden for security</span> */}
              </p>
            )}
          </div>

          {/* File Upload Section */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Upload Financial Statement (PDF)
            </h2>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileUploadForMarkdown(e.target.files[0]);
                }
              }}
              disabled={isUploading}
              className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
            />
            {isUploading && (
              <div className="mt-4">
                <div className="relative w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="absolute top-0 left-0 h-full bg-blue-500"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-500 mt-2">{uploadProgress}%</p>
              </div>
            )}
            {errorMessage && <p className="text-sm text-red-500 mt-4">{errorMessage}</p>}
            {recentFileName && (
              <div className="mt-4">
                <p className="text-sm text-gray-700">
                  <strong>Current File:</strong> {recentFileName}
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 mt-8">
          {/* Financial Ratios Section */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Financial Ratios</h2>
            <FinancialRatio recentFileName={recentFileName} />
          </div>

          {/* Balance Sheet Checker Section */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Compliance Gaps</h2>
            <BalanceSheetChecker recentFileName={recentFileName} />
          </div>

          {/* Auditor's Report Section */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Auditor's Report</h2>
            <AuditorReport recentFileName={recentFileName} />
          </div>

          {/* Director's Report Section */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">Director's Report</h2>
            <DirectorReport recentFileName={recentFileName} />
          </div>

          {/* Testimonials Section */}
          <Testimonials />
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default App;