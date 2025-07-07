import React, { useState } from 'react';
import { useAnalysis } from '../context/AnalysisContext'; // Add this at the top

const DirectorReport: React.FC = () => {
  const { setResults } = useAnalysis(); // Add this inside your component
  const [recentFileName, setRecentFileName] = useState<string | null>(null);
  const [insights, setInsights] = useState(null);
  const [conclusion, setConclusion] = useState('');
  const [summary, setSummary] = useState(''); // New: summary state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showResponse, setShowResponse] = useState(true); // Add this state

  // States for file upload
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');

  // Dummy handler for file upload (replace with actual upload logic as needed)
  const handleFileUploadForMarkdown = async (file: File) => {
    const formData = new FormData();
    formData.append('pdf', file);

    setIsUploading(true);
    setUploadProgress(0);
    setErrorMessage('');
    setRecentFileName(file.name);

    try {
      const response = await fetch('https://finbizinfo.com/api/generate_markdown', {
        method: 'POST',
        body: formData,
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

  const fetchMarkdownFileAndAnalyze = async () => {
    if (!recentFileName) {
      setError('No file selected. Please upload a file first.');
      return;
    }

    const markdownFileName = recentFileName.replace('.pdf', '.md');
    const markdownFilePath = `https://finbizinfo.com/api/saved_markdowns/${encodeURIComponent(markdownFileName)}`;
    const backendUrl = 'https://finbizinfo.com/api/api/analyze-directors-report';
    const summaryUrl = 'https://finbizinfo.com/api/api/summary-directors-report'; // New endpoint for summary

    setLoading(true);
    setError('');
    setInsights(null);
    setConclusion('');
    setSummary(''); // Reset summary

    try {
      // Fetch markdown file
      const fileResponse = await fetch(markdownFilePath);
      if (!fileResponse.ok) {
        throw new Error(`Failed to fetch the markdown file: ${markdownFilePath} (Status: ${fileResponse.status})`);
      }

      const markdownBlob = await fileResponse.blob();
      const formData = new FormData();
      formData.append('md_file', markdownBlob, markdownFileName);

      // Analyze compliance
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

      // Fetch summary (new)
      const summaryResponse = await fetch(summaryUrl, {
        method: 'POST',
        body: formData,
      });
      let summaryText = '';
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        summaryText = summaryData.summary || '';
        setSummary(summaryText);
      } else {
        summaryText = 'Could not generate summary.';
        setSummary(summaryText);
      }

      // Store both compliance and summary in context for Summary.tsx
      setResults((prev: any) => ({
        ...prev,
        director: [
          data.compliance_results ? `**Compliance Results:**\n${data.conclusion || ''}\n${JSON.stringify(data.compliance_results, null, 2)}` : '',
          summaryText ? `**Director's Report Summary:**\n${summaryText}` : ''
        ].filter(Boolean).join('\n\n')
      }));
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
    <div className="bg-white rounded-lg p-6 shadow-sm">
      <h5 className="text-blue-900 text-center">
        📄Upload Director's Report (PDF)
      </h5>
      <div className="flex flex-col items-center justify-center w-full h-32 px-4 py-3 bg-blue-50 text-blue-700 border-2 border-dashed border-blue-400 rounded-xl cursor-pointer transition-colors duration-200 hover:bg-blue-100">
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
        />
        
        {errorMessage && <p className="text-sm text-red-500 mt-4">{errorMessage}</p>}
      </div>

      <div id="upload-section" className="text-center">
        {recentFileName && (
          <p id="file-name" className="text-blue-700 mt-2">
            <strong>Current File:</strong> {recentFileName.replace('.pdf', '.md')}
          </p>
        )}
        <br />
        <button
          id="analyze-button"
          onClick={fetchMarkdownFileAndAnalyze}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          {loading ? <span 
              className="loading-ring"
              style={{
                display: 'inline-block',
                width: '24px',
                height: '24px',
                verticalAlign: 'middle'
               }}
             ></span> : 'Analyze Report'}
        </button>
        {error && <div className="error-message text-red-600 mt-4">{error}</div>}
      </div>

      {/* Show/Hide Response Button */}
      {insights && (
        <div className="text-right mb-2">
          <button
            onClick={() => setShowResponse((prev) => !prev)}
            className={`px-3 py-1 rounded text-sm transition-colors duration-150 
              ${showResponse 
                ? 'bg-gray-200 hover:bg-gray-300 text-gray-50' 
                : 'bg-blue-100 hover:bg-blue-200 text-blue-500 border border-blue-300'
              }`}
            aria-pressed={showResponse}
            disabled={loading}
          >
            {showResponse ? (
              <>
                Hide Response
              </>
            ) : (
              <>
                Show Response
              </>
            )}
          </button>
        </div>
      )}

      {insights && showResponse && (
        <>
          {/* Compliance Results Section */}
          <div id="results-section" className="mt-8">
            <div>
              <h2 className="text-xl font-bold text-center text-black-600 mb-4">Compliance Results</h2>
              <p className="text-center text-blue-700 font-semibold mb-4">{conclusion}</p>
              <div id="results-container">{renderInsights(insights)}</div>
            </div>
          </div>

          {/* Summary Section */}
          <div id="summary-section" className="mt-8">
            {summary && !loading && (
              <div>
                <h2 className="text-xl font-bold text-center text-blue-700 mb-2">Director's Report Summary</h2>
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <pre className="whitespace-pre-wrap break-words text-sm text-blue-800">
                    {summary}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default DirectorReport;
