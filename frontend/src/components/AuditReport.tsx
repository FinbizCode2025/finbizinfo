import React, { useState } from 'react';
import './AuditReport.css';

const AuditorReport: React.FC<{ recentFileName: string | null }> = ({ recentFileName }) => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchMarkdownFileAndAnalyze = async () => {
    if (!recentFileName) {
      setError('No file selected. Please upload a Markdown file first.');
      return;
    }

    const markdownFileName = recentFileName.replace('.pdf', '.md'); // Replace .pdf with .md
    const markdownFilePath = `http://82.180.145.47:5002/saved_markdowns/${encodeURIComponent(markdownFileName)}`; // Encode filename
    const backendUrl = 'http://82.180.145.47:5002/api/analyze-audit-report'; // Backend endpoint

    setLoading(true);
    setError('');
    setInsights(null);

    try {
      console.log(`Fetching markdown file from: ${markdownFilePath}`);
      const fileResponse = await fetch(markdownFilePath);

      if (!fileResponse.ok) {
        throw new Error(`Failed to fetch the markdown file: ${markdownFilePath} (Status: ${fileResponse.status})`);
      }

      const markdownBlob = await fileResponse.blob();
      const formData = new FormData();
      formData.append('md_file', markdownBlob, markdownFileName);

      console.log(`Sending analysis request to: ${backendUrl}`);
      const response = await fetch(backendUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to analyze the report.');
      }

      const data = await response.json();
      console.log('Analysis successful:', data);
      setInsights(data.insights);
    } catch (err) {
      console.error('Error during analysis:', err);
      setError(err instanceof Error ? err.message : 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const renderInsights = (data: any) => {
    if (!data || typeof data !== 'object') {
      return <p>No insights available.</p>;
    }

    return Object.entries(data).map(([key, value]) => (
      <div key={key} className="insight-item">
        <strong>{key.replace(/_/g, ' ')}:</strong>
        {typeof value === 'object' && value !== null ? (
          <div className="nested">
            {Object.entries(value).map(([subKey, subValue]) => (
              <p key={subKey}>
                <strong>{subKey.replace(/_/g, ' ')}:</strong> {subValue}
              </p>
            ))}
          </div>
        ) : (
          <span> {typeof value === 'string' || typeof value === 'number' ? value : JSON.stringify(value)}</span>
        )}
      </div>
    ));
  };

  return (
    <div className="container">
      <h1 className="text-3xl font-bold text-center text-black-600 mb-8">Analyse Auditor's Report</h1>

      <div id="upload-section" className="text-center">
        {recentFileName && (
          <p id="file-name" className="text-gray-700 mt-2">
            <strong>Current File:</strong> {recentFileName.replace('.pdf', '.md')}
          </p>
        )}
        <br />
        <button
          id="analyze-button"
          onClick={fetchMarkdownFileAndAnalyze}
          disabled={!recentFileName || loading}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          {loading ? 'Analyzing...' : 'Analyze Report'}
        </button>
        {loading && <div className="loading-indicator">Analyzing your report... Please wait.</div>}
        {error && <div className="error-message">{error}</div>}
      </div>

      {insights && (
        <div id="results-section">
          <div id="results-container">{renderInsights(insights)}</div>
        </div>
      )}
    </div>
  );
};

export default AuditorReport;
