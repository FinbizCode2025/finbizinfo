import React, { useState } from 'react';

interface DirectorReportProps {
  sessionId: string | null;
  title: string;
}

interface ComplianceResult {
  rule: string;
  status: 'Complied' | 'Not Complied' | 'Not Found';
  reasoning: string;
  error?: string;
}

const getStatusClass = (status: ComplianceResult['status']) => {
  switch (status) {
    case 'Complied':
      return 'bg-green-100 text-green-800';
    case 'Not Complied':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-yellow-100 text-yellow-800';
  }
};

const DirectorReport: React.FC<DirectorReportProps> = ({ sessionId, title }) => {
  const [results, setResults] = useState<ComplianceResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStreamingReport = async () => {
    if (!sessionId) {
      setError('Please upload and process a document to generate this report.');
      return;
    }

    setIsLoading(true);
    setResults([]);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:5002/chat/director-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || `Server responded with status ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get response reader.');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last partial line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue;
          try {
            const result: ComplianceResult = JSON.parse(line);
            if (result.error) {
              setError(`An error occurred during analysis: ${result.error}`);
              break;
            }
            setResults(prev => [...prev, result]);
          } catch (e) {
            console.error('Failed to parse stream line:', line, e);
          }
        }
      }
    } catch (err) {
      console.error(`Error fetching ${title}:`, err);
      setError((err as Error).message || `Failed to fetch ${title} report.`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 border-t border-gray-200 mt-4">
      <button
        onClick={fetchStreamingReport}
        className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-semibold shadow transition disabled:opacity-50"
        disabled={isLoading || !sessionId}
      >
        {isLoading ? 'Generating...' : `Generate ${title}`}
      </button>

      {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">{error}</div>}

      <div className="mt-6 overflow-x-auto">
        {results.length > 0 && (
          <table className="min-w-full bg-white border border-gray-200 rounded-lg shadow-md">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Compliance Rule</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reasoning</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {results.map((result, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{result.rule}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-3 py-1 text-xs font-bold rounded-full ${getStatusClass(result.status)}`}>
                      {result.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{result.reasoning}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {isLoading && (
        <div className="mt-4 flex items-center justify-center text-gray-500">
          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Analyzing compliance rules...</span>
        </div>
      )}
    </div>
  );
};

export default DirectorReport;