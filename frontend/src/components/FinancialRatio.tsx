import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './FinancialRatio.css';
import { useAnalysis } from '../context/AnalysisContext';
import FinancialCharts from './FinancialCharts';

const extractMissingInfoSection = (text: string) => {
  // Regex to extract "Missing Information" section (case-insensitive, until next heading or end)
  const missingInfoRegex = /(^|\n)#+\s*Missing Information[\s\S]*?(?=\n#+\s|\n\s*Summary|\n\s*Conclusion|\n\s*$)/i;
  const match = text.match(missingInfoRegex);
  if (match) {
    return match[0].replace(/^(\n)?#+\s*Missing Information/i, '').trim();
  }
  // Fallback: look for bold or plain "Missing Information"
  const altRegex = /Missing Information[\s\S]*?(?=\n\S|\n\s*Summary|\n\s*Conclusion|\n\s*$)/i;
  const altMatch = text.match(altRegex);
  if (altMatch) {
    return altMatch[0].replace(/Missing Information/i, '').trim();
  }
  return '';
};

const removeMissingInfoSection = (text: string) => {
  // Remove the "Missing Information" section from the text
  const missingInfoRegex = /(^|\n)#+\s*Missing Information[\s\S]*?(?=\n#+\s|\n\s*Summary|\n\s*Conclusion|\n\s*$)/i;
  let cleaned = text.replace(missingInfoRegex, '');
  // Also remove fallback
  const altRegex = /Missing Information[\s\S]*?(?=\n\S|\n\s*Summary|\n\s*Conclusion|\n\s*$)/i;
  cleaned = cleaned.replace(altRegex, '');
  return cleaned.trim();
};

const FinancialRatio = ({ recentFileName }: { recentFileName: string | null }) => {
  const [messages, setMessages] = useState<{ text: string; sender: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResponse, setShowResponse] = useState(true);
  const { setResults } = useAnalysis();

  // New state for missing info
  const [missingInfo, setMissingInfo] = useState<string>('');

  useEffect(() => {
    if (recentFileName) {
      setMissingInfo('');
      setMessages([]);
    }
  }, [recentFileName]);

  const handleAnalyzeMarkdown = async () => {
    if (!recentFileName) {
      alert('No markdown file available for analysis. Please upload a PDF first.');
      return;
    }

    setMessages([]);
    setMissingInfo('');
    const markdownFileName = recentFileName.replace('.pdf', '.md');
    const markdownFilePath = `https://finbizinfo.com/api/saved_markdowns/${markdownFileName}`;

    setIsLoading(true);

    try {
      const fileResponse = await fetch(markdownFilePath);
      if (!fileResponse.ok) {
        throw new Error(`Failed to fetch the markdown file: ${markdownFilePath} (Status: ${fileResponse.status})`);
      }
      const markdownBlob = await fileResponse.blob();
      const formData = new FormData();
      formData.append('markdown', markdownBlob, markdownFileName);

      const backendUrl = 'https://finbizinfo.com/api/analyze_pdf_ratios';
      const response = await fetch(backendUrl, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.response) {
        // Extract missing info section
        const missingSection = extractMissingInfoSection(data.response);
        setMissingInfo(missingSection);

        // Remove missing info from main response
        const cleanedResponse = removeMissingInfoSection(data.response);

        setMessages([{ text: cleanedResponse, sender: 'bot' }]);
        setResults((prev: any) => ({ ...prev, financial: data.response }));
        setShowResponse(true);
      } else {
        const errorMessage = data.error || `Analysis failed with status: ${response.status}`;
        setMessages([{ text: `Error: ${errorMessage}`, sender: 'bot' }]);
        setShowResponse(true);
      }
    } catch (error) {
      setMessages([
        { text: `Error: Could not connect to the analysis server. ${error instanceof Error ? error.message : 'Unknown error'}`, sender: 'bot' },
      ]);
      setShowResponse(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="financial_statement">
        <div className="font-bold text-center text-black-600 mb-8">
          {recentFileName && (
            <p id="file-name" className="text-blue-700 mt-2">
              <strong>Current File:</strong> {recentFileName.replace('.pdf', '.md')}
            </p>
          )}
          <br />
          <button
            onClick={handleAnalyzeMarkdown}
            disabled={isLoading || !recentFileName}
            className="bg-blue-500 hover:bg-blue-700 text-white rounded"
          >
            {isLoading ? (
              <span
                className="loading-ring"
                style={{
                  display: 'inline-block',
                  width: '24px',
                  height: '24px',
                  verticalAlign: 'middle',
                }}
              ></span>
            ) : (
              'Analyse Financial Ratios'
            )}
          </button>
        </div>

        {/* Show/Hide Response Button */}
        {messages.length > 0 && (
          <div className="text-right mb-2">
            <button
              onClick={() => setShowResponse((prev) => !prev)}
              className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm"
            >
              {showResponse ? 'Hide Response' : 'Show Response'}
            </button>
          </div>
        )}

        {/* Missing Information Section */}
        

        {/* Response area */}
        {messages.length > 0 && showResponse && (
          <div className="response mt-6">
            <div
              className="bg-white border border-gray-300 rounded-lg p-4 max-h-[48rem] overflow-y-auto shadow-md"
              style={{
                fontFamily: 'Segoe UI, Arial, sans-serif',
                fontSize: '1.05rem',
                color: '#222',
                transition: 'box-shadow 0.2s',
              }}
            >
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`message mb-4 ${
                    msg.sender === 'bot'
                      ? 'bg-blue-50 border-l-4 border-blue-400'
                      : msg.sender === 'user'
                      ? 'bg-green-50 border-l-4 border-green-400'
                      : 'bg-gray-100 border-l-4 border-gray-400'
                  } p-3 rounded`}
                  style={{
                    boxShadow:
                      msg.sender === 'bot'
                        ? '0 2px 8px 0 rgba(59,130,246,0.07)'
                        : msg.sender === 'user'
                        ? '0 2px 8px 0 rgba(34,197,94,0.07)'
                        : '0 2px 8px 0 rgba(156,163,175,0.07)',
                    color: '#222',
                  }}
                >
                  {msg.sender === 'bot' ? (
                    <div className="bot-message-markdown" style={{ color: '#222' }}>
                      <ReactMarkdown
                        components={{
                          h1: ({ node, ...props }) => (
                            <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#222', margin: '0.5em 0' }} {...props} />
                          ),
                          h2: ({ node, ...props }) => (
                            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#222', margin: '0.5em 0' }} {...props} />
                          ),
                          li: ({ node, ...props }) => (
                            <li style={{ marginLeft: '1.2em', listStyle: 'disc', color: '#222' }} {...props} />
                          ),
                          strong: ({ node, ...props }) => (
                            <strong style={{ color: '#111' }} {...props} />
                          ),
                          p: ({ node, ...props }) => (
                            <p style={{ margin: '0.5em 0', color: '#222' }} {...props} />
                          ),
                          code: ({ node, ...props }) => (
                            <code
                              style={{
                                background: '#f1f1f1',
                                borderRadius: 4,
                                padding: '2px 6px',
                                fontSize: '0.98em',
                                color: '#222',
                              }}
                              {...props}
                            />
                          ),
                          table: ({ node, ...props }) => (
                            <table
                              style={{
                                width: '100%',
                                borderCollapse: 'collapse',
                                margin: '0.5em 0',
                                color: '#222',
                              }}
                              {...props}
                            />
                          ),
                          th: ({ node, ...props }) => (
                            <th
                              style={{
                                border: '1px solid #bbb',
                                background: '#f3f3f3',
                                padding: '4px 8px',
                                color: '#222',
                              }}
                              {...props}
                            />
                          ),
                          td: ({ node, ...props }) => (
                            <td
                              style={{
                                border: '1px solid #bbb',
                                padding: '4px 8px',
                                color: '#222',
                              }}
                              {...props}
                            />
                          ),
                        }}
                      >
                        {msg.text}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <pre style={{ whiteSpace: 'pre-wrap', color: '#0f172a', margin: 0 }}>{msg.text}</pre>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      <div>
        <FinancialCharts
          markdown={messages.length > 0 ? messages[0].text : ''}
        />
      </div>
    </div>
  );
};

export default FinancialRatio;
