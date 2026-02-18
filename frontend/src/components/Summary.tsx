import React, { useState } from 'react';
import { useAnalysis } from '../context/AnalysisContext';
import ReactMarkdown from 'react-markdown';

const Summary: React.FC = () => {
  const { results } = useAnalysis();
  const [combinedSummary, setCombinedSummary] = useState<string>('');
  const [showSummary, setShowSummary] = useState<boolean>(false);
  const [finalSummary, setFinalSummary] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  // Summarize the combinedSummary using the API
  const summarizeCombinedSummary = async (text: string) => {
    setLoading(true);
    setFinalSummary('');
    try {
      const response = await fetch('https://finbizinfo.com/api/api/summarize-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      if (response.ok && data.summary) {
        setFinalSummary(data.summary);
      } else {
        setFinalSummary('Failed to summarize the report.');
      }
    } catch (error) {
      setFinalSummary('Error connecting to summary service.');
    }
    setLoading(false);
  };

  const handleSummarize = () => {
    const parts = [];
    if (results.financial) parts.push(`**Financial Ratios:**\n${results.financial}`);
    if (results.audit) parts.push(`**Auditor's Report:**\n${results.audit}`);
    if (results.director) parts.push(`**Director's Report:**\n${results.director}`);
    const summaryText = parts.length === 0 ? 'No reports available to summarize.' : parts.join('\n\n');
    setCombinedSummary(summaryText);
    setShowSummary(true);
    setFinalSummary('');
    if (parts.length > 0) {
      summarizeCombinedSummary(summaryText);
    }
  };

  return (
    <div>
      <div className="flex flex-wrap gap-4 mb-6 justify-center">
        <button
          className="px-6 py-2 bg-blue-700 text-white rounded-lg shadow hover:bg-blue-800 transition font-semibold text-base focus:outline-none focus:ring-2 focus:ring-blue-400"
          onClick={handleSummarize}
        >
          View Summarised Reports
        </button>
        {combinedSummary && (
          <button
            className="px-6 py-2 bg-gray-700 text-white rounded-lg shadow hover:bg-gray-800 transition font-semibold text-base focus:outline-none focus:ring-2 focus:ring-gray-400"
            onClick={() => setShowSummary((prev) => !prev)}
          >
            {showSummary ? 'Hide Summary' : 'Show Summary'}
          </button>
        )}
      </div>
      {showSummary && combinedSummary && (
        <div className="mb-4">
          <div className="flex items-center mb-2">
            <svg className="w-6 h-6 text-blue-900 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2a4 4 0 014-4h2a4 4 0 014 4v2M7 7a4 4 0 018 0v2a4 4 0 01-8 0V7z" />
            </svg>
            <h3 className="text-lg font-semibold text-blue-900">Summary</h3>
          </div>
          <div
            className="bg-blue-50 border border-blue-200 rounded-lg p-6 shadow-inner min-h-[120px]"
            style={{ fontFamily: 'Segoe UI, Arial, sans-serif' }}
          >
            {loading ? (
              <div className="flex items-center justify-center h-24">
                <svg className="animate-spin h-8 w-8 text-blue-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                </svg>
                <span className="ml-3 text-blue-900 font-semibold">Generating summary...</span>
              </div>
            ) : (
              <div
                className="prose max-w-none text-base"
                style={{
                  color: '#111111', // black
                  fontWeight: 500,
                  letterSpacing: '0.01em',
                  fontFamily: 'Segoe UI, Arial, sans-serif'
                }}
              >
                <ReactMarkdown
                  components={{
                    h1: ({node, ...props}) => <h1 style={{color: '#111111', fontWeight: 700}} {...props} />,
                    h2: ({node, ...props}) => <h2 style={{color: '#111111', fontWeight: 700}} {...props} />,
                    h3: ({node, ...props}) => <h3 style={{color: '#111111', fontWeight: 700}} {...props} />,
                    strong: ({node, ...props}) => <strong style={{color: '#111111'}} {...props} />,
                    p: ({node, ...props}) => <p style={{color: '#111111', marginBottom: '0.5em'}} {...props} />,
                    li: ({node, ...props}) => <li style={{color: '#111111'}} {...props} />,
                  }}
                >
                  {finalSummary || combinedSummary}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Summary;