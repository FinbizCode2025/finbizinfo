import React, { useState } from 'react';
import './DirectorReport.css';

const DirectorReport: React.FC<{ recentFileName: string | null }> = ({ recentFileName }) => {
  const [insights, setInsights] = useState(null);
  const [conclusion, setConclusion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchMarkdownFileAndAnalyze = async () => {
    if (!recentFileName) {
      setError('No file selected. Please upload a Markdown file first.');
      return;
    }

    const markdownFileName = recentFileName.replace('.pdf', '.md');
    const markdownFilePath = `http://82.180.145.47:5002/saved_markdowns/${encodeURIComponent(markdownFileName)}`;
    const backendUrl = 'http://82.180.145.47:5002/api/analyze-directors-report';

    setLoading(true);
    setError('');
    setInsights(null);
    setConclusion('');

    try {
      const fileResponse = await fetch(markdownFilePath);
      if (!fileResponse.ok) {
        throw new Error(`Failed to fetch the markdown file: ${markdownFilePath} (Status: ${fileResponse.status})`);
      }

      const markdownBlob = await fileResponse.blob();
      const formData = new FormData();
      formData.append('md_file', markdownBlob, markdownFileName);

      const response = await fetch(backendUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to analyze the report.');
      }

      const data = await response.json();
      setInsights(data.compliance_results);
      setConclusion(data.conclusion || '');
    } catch (err) {
      console.error('Error during analysis:', err);
      setError(err instanceof Error ? err.message : 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const renderInsights = (data: any) => {
    if (!data || !Array.isArray(data)) {
      return <p>No compliance results available.</p>;
    }

    return (
      <table className="insights-table">
        <thead>
          <tr>
            <th>Rule</th>
            <th>Status</th>
            <th>Remarks</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item: any, index: number) => (
            <tr key={index}>
              <td>{item.rule}</td>
              <td>{item.status}</td>
              <td>{item.remarks || 'N/A'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="container">
      <h1 className="text-3xl font-bold text-center text-black-600 mb-8">Analyse Director's Report</h1>

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
        {error && <div className="error-message text-red-600 mt-4">{error}</div>}
      </div>

      {insights && (
        <div id="results-section" className="mt-8">
          <h2 className="text-xl font-bold text-center text-black-600 mb-4">Compliance Results</h2>
          <p className="text-center text-green-700 font-semibold mb-4">{conclusion}</p>
          <div id="results-container">{renderInsights(insights)}</div>
        </div>
      )}
    </div>
  );
};

export default DirectorReport;
