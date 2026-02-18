import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './FinancialRatio.css';
import { useAnalysis } from '../context/AnalysisContext';

const extractMissingInfoSection = (text: string) => {
  const missingInfoRegex = /(^|\n)#+\s*Missing Information[\s\S]*?(?=\n#+\s|\n\s*Summary|\n\s*Conclusion|\n\s*$)/i;
  const match = text.match(missingInfoRegex);
  if (match) return match[0].replace(/^\n?#+\s*Missing Information/i, '').trim();
  const altRegex = /Missing Information[\s\S]*?(?=\n\S|\n\s*Summary|\n\s*Conclusion|\n\s*$)/i;
  const altMatch = text.match(altRegex);
  if (altMatch) return altMatch[0].replace(/Missing Information/i, '').trim();
  return '';
};

const removeMissingInfoSection = (text: string) => {
  const missingInfoRegex = /(^|\n)#+\s*Missing Information[\s\S]*?(?=\n#+\s|\n\s*Summary|\n\s*Conclusion|\n\s*$)/i;
  let cleaned = text.replace(missingInfoRegex, '');
  const altRegex = /Missing Information[\s\S]*?(?=\n\S|\n\s*Summary|\n\s*Conclusion|\n\s*$)/i;
  cleaned = cleaned.replace(altRegex, '');
  return cleaned.trim();
};

const AuditReport = ({
  endpoint,
  sessionId,
}: {
  endpoint: string;
  sessionId: string;
}) => {
  const [messages, setMessages] = useState<{ text: string; sender: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResponse, setShowResponse] = useState(true);
  const { setResults } = useAnalysis();
  const [, setMissingInfo] = useState<string>('');

  const handleAnalyzeFromFAISS = async () => {
    setMessages([]);
    setMissingInfo('');
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);

      const response = await fetch(`http://127.0.0.1:5002${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.response) {
        const missingSection = extractMissingInfoSection(data.response);
        setMissingInfo(missingSection);
        const cleanedResponse = removeMissingInfoSection(data.response);
        setMessages([{ text: cleanedResponse, sender: 'bot' }]);
        setResults((prev: any) => ({ ...prev, financial: data.response }));
        setShowResponse(true);
      } else {
        const errorMessage = data.error || `Analysis failed with status: ${response.status}`;
        setMessages([{ text: `❌ Error: ${errorMessage}`, sender: 'bot' }]);
        setShowResponse(true);
      }
    } catch (error) {
      setMessages([
        {
          text: `❌ Error: Could not connect to server. ${error instanceof Error ? error.message : 'Unknown error'}`,
          sender: 'bot',
        },
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
          <button
            onClick={handleAnalyzeFromFAISS}
            disabled={isLoading}
            className="bg-blue-500 hover:bg-blue-700 text-white rounded px-4 py-2"
          >
            {isLoading ? (
              <span
                className="loading-ring"
                style={{ display: 'inline-block', width: '24px', height: '24px', verticalAlign: 'middle' }}
              ></span>
            ) : (
              'Analyze Financial Ratios'
            )}
          </button>
        </div>

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

        {messages.length > 0 && showResponse && (
          <div className="response mt-6">
            <div
              className="bg-white border border-gray-300 rounded-lg p-4 max-h-[48rem] overflow-y-auto shadow-md"
              style={{ fontFamily: 'Segoe UI, Arial, sans-serif', fontSize: '1.05rem', color: '#222' }}
            >
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`message mb-4 ${
                    msg.sender === 'bot'
                      ? 'bg-blue-50 border-l-4 border-blue-400'
                      : 'bg-gray-100 border-l-4 border-gray-400'
                  } p-3 rounded`}
                >
                  <div className="bot-message-markdown">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditReport;
