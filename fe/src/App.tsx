import React, { useState, useEffect, useRef, FormEvent, ChangeEvent } from 'react';
import axios from 'axios';
import DirectorReport from './components/DirectorReport';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
// 💡 CHANGE 1: Use the new component name. Ensure your file is named ReportFormatter.tsx
import ReportFormatter from './components/ReportFormatter.tsx';
import { AutoTable } from './utils/tableUtils';
import RatioDetails from './components/RatioDetails';
import FinancialInsightsReport from './components/FinancialInsightsReport';
import ComprehensiveFinancialReport from './components/ComprehensiveFinancialReport';
import MultiAgentAnalysis from './components/MultiAgentAnalysis'; // Multi-agent system component
import PeerComparison from './PeerComparison.jsx';



// --- Type Definitions ---

interface ChatMessage {
  sender: 'user' | 'ai' | 'system';
  text: string;
}

interface TokenStats {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  tokens_used: number;
}

interface RatioData {
  name: string;
  value: number;
}

interface ChatPanelProps {
  sessionId: string | null;
  onClose: () => void;
}

interface ReportSectionProps {
  endpoint: string;
  sessionId: string | null;
  title: string;
  onDataUpdate?: (data: any) => void;
}

interface FinancialChartsProps {
  sessionId: string | null;
  ratioData?: any;
  loading?: boolean;
}

interface HeroProps {
  handleUpload: (file: File) => Promise<void>;
  file: File | null;
  uploadStatus: string;
  apiKeyStatus: string;
}


// --- Local Component Definitions ---

// 1. Chat Panel (The actual chat window content)
const ChatPanel: React.FC<ChatPanelProps> = ({ sessionId, onClose }) => {
  const [chatInput, setChatInput] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState<boolean>(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSendMessage = async () => {
    const message = chatInput.trim();
    if (!message || !sessionId) return;

    setChatMessages(prev => [...prev, { sender: 'user', text: message }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await axios.post(
        'http://127.0.0.1:5002/chat',
        { session_id: sessionId, prompt: message },
        { headers: { 'Content-Type': 'application/json' } }
      );

      setChatMessages(prev => [...prev, { sender: 'ai', text: res.data.response }]);
    } catch (error) {
      setChatMessages(prev => [...prev, { sender: 'system', text: 'Error: Could not connect to chat service.' }]);
    }
    setChatLoading(false);
  };

  return (
    <div className="fixed bottom-4 right-4 m-0 w-full max-w-sm bg-white border border-gray-200 rounded-xl shadow-2xl z-20 transition-transform duration-300 ease-in-out transform scale-100 opacity-100">
      <div className="p-4 bg-blue-600 text-white rounded-t-xl font-semibold flex justify-between items-center">
        <span>Document Chat</span>
        <button
          onClick={onClose}
          className="p-1 rounded-full hover:bg-blue-700 transition"
          aria-label="Close Chat"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className="h-64 overflow-y-auto p-4 space-y-3 bg-gray-50">
        {chatMessages.length === 0 && (
          <p className="text-gray-500 text-sm italic">Chat ready when document is uploaded and processed.</p>
        )}
        {chatMessages.map((msg, index) => (
          <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`p-3 max-w-[85%] rounded-lg text-sm shadow-md ${msg.sender === 'user' ? 'bg-blue-100 text-gray-800' : 'bg-gray-200 text-gray-800'
              }`}>
              {msg.text}
            </div>
          </div>
        ))}
        {chatLoading && (
          <div className="flex justify-start">
            <div className="p-3 bg-gray-200 rounded-lg text-sm text-gray-700 animate-pulse">AI is thinking...</div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>
      <div className="p-4 border-t border-gray-200 flex">
        <input
          type="text"
          value={chatInput}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setChatInput(e.target.value)}
          onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleSendMessage()}
          placeholder={sessionId ? "Ask a question..." : "Upload document first"}
          className="flex-1 border border-gray-300 rounded-l-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={!sessionId || chatLoading}
        />
        <button
          onClick={handleSendMessage}
          disabled={!sessionId || chatLoading || !chatInput.trim()}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-r-lg transition disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
};


// Helper function to render JSON object as formatted HTML
// This function is shared between ReportSection and HighlightedReportSection
const renderJsonObject = (obj: any, depth: number = 0): React.ReactNode => {
  if (obj === null || obj === undefined) return 'null';

  if (typeof obj === 'string') {
    return <span className="text-green-700">"{obj}"</span>;
  }

  if (typeof obj === 'number') {
    return <span className="text-blue-700">{obj}</span>;
  }

  if (typeof obj === 'boolean') {
    return <span className="text-purple-700">{String(obj)}</span>;
  }

  if (Array.isArray(obj)) {
    return (
      <div className="ml-4">
        <span className="text-gray-700">[</span>
        {obj.map((item, idx) => (
          <div key={idx} className="text-gray-700">
            {renderJsonObject(item, depth + 1)}
            {idx < obj.length - 1 && ','}
          </div>
        ))}
        <span className="text-gray-700">]</span>
      </div>
    );
  }

  if (typeof obj === 'object') {
    const keys = Object.keys(obj);
    return (
      <div className="ml-4">
        <span className="text-gray-700">{'{'}</span>
        {keys.map((key, idx) => (
          <div key={key} className="text-gray-700">
            <span className="text-red-700">"{key}"</span>
            <span>: </span>
            {renderJsonObject(obj[key], depth + 1)}
            {idx < keys.length - 1 && ','}
          </div>
        ))}
        <span className="text-gray-700">{'}'}</span>
      </div>
    );
  }

  return String(obj);
};

// 2. Generic Report Section (Used only for Ratios, where JSON data is expected)
const ReportSection: React.FC<ReportSectionProps> = ({ endpoint, sessionId, title, onDataUpdate }) => {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [viewMode, setViewMode] = useState<'table' | 'detailed'>('table');

  const fetchData = async () => {
    if (!sessionId) {
      setData(null);
      setError('Please upload and process a document to generate this report.');
      return;
    }
    setIsLoading(true);
    setError('');
    setData(null);
    try {
      // Pre-check that server still has this session stored.
      try {
        await axios.get(`http://127.0.0.1:5002/upload/status/${sessionId}`);
      } catch (statusErr) {
        setIsLoading(false);
        setError('Session not found or expired on server. Please re-upload the document.');
        if (onDataUpdate) onDataUpdate(null);
        return;
      }
      const res = await axios.post(
        `http://127.0.0.1:5002${endpoint}`,
        { session_id: sessionId },
        { headers: { 'Content-Type': 'application/json' } }
      );

      const resp = res.data.response;
      if (resp && typeof resp === 'object') {
        setData(resp);
        if (onDataUpdate) onDataUpdate(res.data);
      } else if (typeof resp === 'string') {
        setData({ message: resp });
        if (onDataUpdate) onDataUpdate({ response: resp });
      } else {
        setError('No data found or error in response structure.');
        if (onDataUpdate) onDataUpdate(null);
      }
    } catch (err) {
      console.error(`Error fetching ${title}:`, err);
      const errMsg = (err as any)?.response?.data?.error || (err as any)?.message || `Failed to fetch ${title} report. Please check the backend connection and try again.`;
      setError(errMsg);
      if (onDataUpdate) onDataUpdate(null);
    }
    setIsLoading(false);
  };

  const fetchDebugAnalyze = async () => {
    if (!sessionId) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await axios.post(
        `http://127.0.0.1:5002/debug/analyze-session/${sessionId}`,
        {},
        { headers: { 'Content-Type': 'application/json' } }
      );

      // Wrap debug response so UI expects `response` object as usual
      const debugResp = { response: res.data.ratios_result || res.data };
      setData(debugResp.response);
      if (onDataUpdate) onDataUpdate({ response: debugResp.response, debug: res.data });
    } catch (err) {
      console.error('Debug analyze error:', err);
      const errMsg = (err as any)?.response?.data?.error || (err as any)?.message || 'Debug analyze failed.';
      setError(errMsg);
    }
    setIsLoading(false);
  };

  const searchCompanyWeb = async () => {
    if (!sessionId) return;
    const inferred = '';
    const name = window.prompt('Company name to search (leave blank to infer):', inferred) || inferred;
    if (!name) {
      setError('Company name required for web search.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const res = await axios.post('http://127.0.0.1:5002/search/company', { company_name: name, session_id: sessionId });
      const payload = res.data;
      // Show combined result in UI via setData
      setData({ response: payload.web_result || payload });
      if (onDataUpdate) onDataUpdate({ response: payload.web_result || payload, debug: payload });
    } catch (err) {
      const errMsg = (err as any)?.response?.data?.error || (err as any)?.message || 'Web search failed.';
      setError(errMsg);
    }
    setIsLoading(false);
  };

  // Check if this is a financial ratio response (be tolerant of different backend shapes)
  // data might be the raw response object {response: {...}, balance_sheet_data: [...]}
  // or it might be just the response payload
  const actualData = data?.response || data;
  const isFinancialRatio = endpoint.includes('financial-ratio') && (
    Boolean(actualData?.ratios) || Boolean(actualData?.financial_ratios) || Boolean(actualData?.ratio) || Boolean(actualData?.liquidity_ratios) || Boolean(actualData?.current_ratio)
  );

  return (
    <div className="p-4 border-t border-gray-200 mt-4">
      <button
        onClick={fetchData}
        className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-semibold shadow transition disabled:opacity-50"
        disabled={isLoading || !sessionId}
      >
        {isLoading ? 'Generating...' : `Generate ${title}`}
      </button>
      <button
        onClick={fetchDebugAnalyze}
        className="ml-2 px-3 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-semibold shadow transition disabled:opacity-50"
        disabled={isLoading || !sessionId}
        title="Run AI+deterministic extractor and compute ratios for debugging"
      >
        🔍 AI Extract & Compute
      </button>
      <button
        onClick={searchCompanyWeb}
        className="ml-2 px-3 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-semibold shadow transition disabled:opacity-50"
        disabled={isLoading || !sessionId}
        title="Search the web for this company and merge with PDF data"
      >
        🌐 Search Web
      </button>

      {isFinancialRatio && data && (
        <div className="flex gap-2 mt-4 mb-4">
          <button
            onClick={() => setViewMode('table')}
            className={`px-4 py-2 rounded-lg font-semibold transition ${viewMode === 'table'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
              }`}
          >
            📊 Table View
          </button>
          <button
            onClick={() => setViewMode('detailed')}
            className={`px-4 py-2 rounded-lg font-semibold transition ${viewMode === 'detailed'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
              }`}
          >
            📈 Detailed Analysis
          </button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {data && (
        <div className="mt-4">
          {isFinancialRatio && viewMode === 'detailed' ? (
            <RatioDetails ratios={flattenRatios(actualData.ratios)} />
          ) : (
            <div className="p-4 bg-white border border-gray-300 rounded-lg shadow-md overflow-auto">
              <AutoTable data={actualData} />
            </div>
          )}
          {/* Debug panel: show deterministic fallback ratios and extracted numbers for transparency */}
          <div className="mt-4">
            {actualData?.deterministic_ratios && (
              <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
                <h4 className="font-semibold">Deterministic / Notes-based Ratios (fallback)</h4>
                <div className="mt-2 text-sm text-gray-800">
                  {renderJsonObject(actualData.deterministic_ratios)}
                </div>
              </div>
            )}

            {actualData?.ratios && (!actualData.deterministic_ratios) && (
              <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded">
                <h4 className="font-semibold">Computed Ratios</h4>
                <div className="mt-2 text-sm text-gray-800">
                  {renderJsonObject(actualData.ratios)}
                </div>
              </div>
            )}

            {/* Expose debug extraction artifacts when present */}
            <div className="space-y-3">
              {actualData?.table_rows && (
                <div className="p-3 bg-gray-50 border border-gray-200 rounded">
                  <strong>Extracted Table Rows:</strong>
                  <div className="mt-2 text-sm text-gray-700 overflow-auto max-h-40">{renderJsonObject(actualData.table_rows)}</div>
                </div>
              )}

              {actualData?._extracted_numbers && (
                <div className="p-3 bg-gray-50 border border-gray-200 rounded">
                  <strong>Extracted Numbers:</strong>
                  <div className="mt-2 text-sm text-gray-700">{renderJsonObject(actualData._extracted_numbers)}</div>
                </div>
              )}

              {data?.balance_sheet_data && (
                <div className="p-3 bg-gray-50 border border-gray-200 rounded">
                  <strong>Balance Sheet Data (raw):</strong>
                  <div className="mt-2 text-sm text-gray-700 overflow-auto max-h-40">{renderJsonObject(data.balance_sheet_data)}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!isLoading && !error && !data && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg text-gray-600 text-center">
          Click "Generate {title}" to see results
        </div>
      )}
    </div>
  );
};


// 3. Highlighted Report Section (UPDATED: Does not use keywords prop)
// 💡 CHANGE 2: Removed keywords from props interface
// interface HighlightedReportSectionProps extends ReportSectionProps {
//   keywords: string[];
// }

const HighlightedReportSection: React.FC<ReportSectionProps> = ({ endpoint, sessionId, title }) => {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [stringData, setStringData] = useState<string>('');

  const fetchData = async () => {
    if (!sessionId) {
      setError('Please upload and process a document to generate this report.');
      setData(null);
      setStringData('');
      return;
    }
    setIsLoading(true);
    setError('');
    setData(null);
    setStringData('');
    try {
      // Pre-check that server still has this session stored.
      try {
        await axios.get(`http://127.0.0.1:5002/upload/status/${sessionId}`);
      } catch (statusErr) {
        setIsLoading(false);
        setError('Session not found or expired on server. Please re-upload the document.');
        return;
      }
      const res = await axios.post(
        `http://127.0.0.1:5002${endpoint}`,
        { session_id: sessionId },
        { headers: { 'Content-Type': 'application/json' } }
      );

      const resp = res.data.response;
      if (resp && typeof resp === 'object') {
        // For objects, store as object for JSON formatting
        setData(resp);
        setStringData('');
      } else if (typeof resp === 'string') {
        // For strings, use ReportFormatter
        setStringData(resp);
        setData(null);
      } else {
        setError('No data found or error in response structure.');
      }
    } catch (error) {
      console.error(`Error fetching ${title}:`, error);
      const errMsg = (error as any)?.response?.data?.error || (error as any)?.message || `Failed to fetch ${title} report. Please check the backend connection and try again.`;
      setError(errMsg);
    }
    setIsLoading(false);
  };

  return (
    <div className="p-4 border-t border-gray-200 mt-4">
      <button
        onClick={fetchData}
        className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-semibold shadow transition disabled:opacity-50"
        disabled={isLoading || !sessionId}
      >
        {isLoading ? 'Generating...' : `Generate ${title}`}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {stringData && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg whitespace-pre-wrap text-gray-700 min-h-[100px] shadow-inner">
          <ReportFormatter text={stringData} />
        </div>
      )}

      {data && (
        <div className="mt-4 p-4 bg-white border border-gray-300 rounded-lg shadow-md overflow-auto">
          <AutoTable data={data} />
        </div>
      )}
    </div>
  );
};


// Helper to flatten nested ratios structure from backend
const flattenRatios = (nestedRatios: any): any => {
  const flattened: any = {};

  try {
    if (typeof nestedRatios === 'object' && nestedRatios !== null) {
      // Iterate through each category (liquidity_ratios, solvency_ratios, etc.)
      for (const [categoryKey, categoryValue] of Object.entries(nestedRatios)) {
        if (categoryKey === 'interpretation' || categoryKey === 'summary') {
          // Skip these special keys
          continue;
        }

        // If the value is an object (a category of ratios), flatten it
        if (typeof categoryValue === 'object' && categoryValue !== null) {
          for (const [ratioKey, ratioValue] of Object.entries(categoryValue)) {
            flattened[ratioKey] = ratioValue;
          }
        }
      }
    }
    return flattened;
  } catch (e) {
    console.error('Error flattening ratios:', e);
    return nestedRatios; // Return original if flattening fails
  }
};

// Helper to extract numeric values from JSON data
const extractNumericFromRatios = (ratios: any): RatioData[] => {
  const extractNumeric = (v: any): number => {
    if (v == null) return 0;
    if (typeof v === 'number') return v;
    if (typeof v === 'string') {
      const cleaned = v.replace(/[,\s]/g, '');
      const n = parseFloat(cleaned);
      return isNaN(n) ? 0 : n;
    }
    if (Array.isArray(v) && v.length > 0) return extractNumeric(v[0]);
    if (typeof v === 'object') {
      for (const key of Object.keys(v)) {
        const n = extractNumeric(v[key]);
        if (n) return n;
      }
    }
    return 0;
  };

  try {
    // If it's a string, try to parse it as JSON
    const data = typeof ratios === 'string' ? JSON.parse(ratios) : ratios;

    if (data && typeof data === 'object') {
      const formatted = Object.entries(data).map(([key, value]) => ({
        name: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        value: extractNumeric(value),
      }));
      return formatted.filter(r => r.value !== 0);
    }
  } catch (e) {
    console.error('Error parsing ratio data:', e);
  }
  return [];
};

// 4. Financial Charts Component
const FinancialCharts: React.FC<FinancialChartsProps> = ({ sessionId, ratioData, loading }) => {
  const COLORS: string[] = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A020F0'];
  const parsedRatios = ratioData ? extractNumericFromRatios(ratioData) : [];

  return (
    <div className="mt-8 p-6 bg-white border border-gray-200 rounded-xl shadow-lg">
      <h3 className="text-xl font-bold mb-4 text-blue-700">Visual Financial Metrics</h3>

      {!sessionId && (
        <p className="text-gray-500 italic">Upload a document to see dynamic charts.</p>
      )}

      {loading && <p className="text-gray-500 italic">Generating financial ratios...</p>}

      {!loading && parsedRatios.length > 0 && (
        <div className="flex flex-col lg:flex-row gap-8 justify-center items-center">
          {/* Pie Chart */}
          <div className="w-full lg:w-1/2 h-80">
            <h4 className="text-lg font-semibold mb-2">Key Ratios</h4>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={parsedRatios}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  label
                >
                  {parsedRatios.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => value.toFixed(2)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Bar Chart */}
          <div className="w-full lg:w-1/2 h-80">
            <h4 className="text-lg font-semibold mb-2">Ratio Comparison</h4>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={parsedRatios}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#8884d8" name="Ratio Value" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {!loading && !ratioData && sessionId && (
        <p className="text-gray-500 italic">No ratio data available yet. Please generate the report above.</p>
      )}
    </div>
  );
};


// 5. Simplified Header 
const Header: React.FC = () => (
  <header className="bg-white shadow-md sticky top-0 z-10">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center h-16">
        <div className="text-2xl font-extrabold text-blue-700 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0h3m-3 0h3m0 0v-6a2 2 0 012-2h2a2 2 0 012 2v6a2 2 0 01-2 2h-2a2 2 0 01-2-2v-6m0-2h2M6 15h2m-2 2h2m-4 0h14" />
          </svg>
          <span className="hidden sm:inline">Financial Document Analyzer</span>
          <span className="sm:hidden">Fin-Doc AI</span>
        </div>
        <nav>
          <a href="#reports" className="text-sm font-medium text-gray-500 hover:text-blue-600 transition ml-4">Reports</a>
          <a href="#about" className="text-sm font-medium text-gray-500 hover:text-blue-600 transition ml-4">About</a>
        </nav>
      </div>
    </div>
  </header>
);

// 6. Hero Section 
const Hero: React.FC<HeroProps> = ({ handleUpload, file, uploadStatus, apiKeyStatus }) => (
  <div className="bg-gradient-to-r from-indigo-500 to-blue-600 text-white pt-16 pb-20 px-4 sm:px-6 lg:px-8 mb-8">
    <div className="max-w-7xl mx-auto text-center">
      <h1 className="text-4xl sm:text-5xl font-extrabold mb-4">
        Unlock Insights from your Financial Documents
      </h1>
      <p className="text-xl opacity-90 mb-8 max-w-3xl mx-auto">
        Upload your annual report PDF and instantly generate deep financial analysis, compliance gap reports, and key summaries using Gemini AI.
      </p>
      <div className="flex flex-col items-center justify-center">
        <label
          htmlFor="hero-pdf-upload"
          className="cursor-pointer flex items-center gap-3 bg-white text-blue-600 font-bold rounded-xl px-8 py-3 shadow-2xl hover:bg-gray-100 transition duration-300 transform hover:scale-[1.02]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5-5m0 0l5 5m-5-5v12" />
          </svg>
          {file ? 'Selected: ' + (file.name.length > 30 ? file.name.substring(0, 27) + '...' : file.name) : 'Upload PDF Report'}
        </label>
        <input
          type="file"
          accept=".pdf"
          id="hero-pdf-upload"
          className="hidden"
          onChange={async (e: ChangeEvent<HTMLInputElement>) => {
            const selectedFile = e.target.files?.[0] || null;
            if (selectedFile) await handleUpload(selectedFile);
          }}
        />
      </div>
      <p className="mt-4 text-sm font-semibold min-h-[1.5em] text-gray-200">
        {uploadStatus}
        {apiKeyStatus && <span className="ml-4 text-green-300">({apiKeyStatus})</span>}
      </p>
    </div>
  </div>
);

// 7. Footer Section
const Footer: React.FC = () => (
  <footer className="bg-gray-800 text-white p-6 mt-12">
    <div className="max-w-7xl mx-auto text-center text-sm">
      &copy; {new Date().getFullYear()} Fin-Doc AI. All rights reserved. Powered by Google Gemini.
    </div>
  </footer>
);

// 8. Testimonials Section
const Testimonials: React.FC = () => (
  <section className="py-12 bg-white rounded-xl shadow-lg mt-8" id="about">
    <div className="max-w-4xl mx-auto px-4 text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-8">What Our Users Say</h2>
      <div className="grid md:grid-cols-2 gap-8">
        <div className="p-6 bg-gray-50 rounded-lg shadow-md">
          <p className="italic text-gray-600">"The speed at which the audit report summary was generated is incredible. It cut down my research time by half."</p>
          <p className="mt-4 font-semibold text-blue-700">- Senior Analyst, Financial Services</p>
        </div>
        <div className="p-6 bg-gray-50 rounded-lg shadow-md">
          <p className="italic text-gray-600">"Compliance Gaps section is a game-changer for due diligence. Highly recommended for quick insights."</p>
          <p className="mt-4 font-semibold text-blue-700">- Compliance Officer, Tech Startup</p>
        </div>
      </div>
    </div>
  </section>
);

// 9. Chat Toggle Button
const ChatButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button
    onClick={onClick}
    className="fixed bottom-6 right-6 p-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-2xl z-30 transition-all duration-300 transform hover:scale-110 active:scale-100"
    aria-label="Open Chatbot"
  >
    <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
    </svg>
  </button>
);

// --- Main Application Component ---

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState<string>('');
  const [apiKeyStatus, setApiKeyStatus] = useState<string>('');
  const [visibleSection, setVisibleSection] = useState<string>('');
  const [showChat, setShowChat] = useState<boolean>(false);
  const [latestRatioData, setLatestRatioData] = useState<any>(null);
  const [tokenStats, setTokenStats] = useState<TokenStats>({
    input_tokens: 0,
    output_tokens: 0,
    total_tokens: 0,
    tokens_used: 0,
  });
  const [showApiInfo, setShowApiInfo] = useState<boolean>(false);
  const [jurisdictions, setJurisdictions] = useState<string[]>([]);
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string | null>(null);
  const [jurisdictionMsg, setJurisdictionMsg] = useState<string>('');
  const [ruleText, setRuleText] = useState<string>('');
  const [ruleLoading, setRuleLoading] = useState<boolean>(false);

  // 💡 DELETION: Removed the FINANCIAL_KEYWORDS array as it is no longer used.

  // For polling status, using NodeJS.Timeout as the type for setInterval return
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Poll backend for processing status
  const pollProcessingStatus = (currentSessionId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`http://127.0.0.1:5002/upload/status/${currentSessionId}`);
        const data = await res.json();
        if (data.status) {
          setUploadStatus(data.status);
          if (
            data.status.toLowerCase().includes('completed') ||
            data.status.toLowerCase().includes('error') ||
            data.status.toLowerCase().includes('failed')
          ) {
            if (pollingRef.current) clearInterval(pollingRef.current);
          }
        }
      } catch {
        // Ignore polling errors
      }
    }, 1000);
  };

  // Set new API key
  const handleSetApiKey = async (e: FormEvent) => {
    e.preventDefault();
    if (!apiKeyInput.trim()) {
      setApiKeyStatus('Key cannot be empty.');
      return;
    }

    setApiKeyStatus('Saving...');
    try {
      const res = await fetch('http://127.0.0.1:5002/api/set-api-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKeyInput }),
      });
      const data = await res.json();
      if (res.ok) {
        setApiKeyStatus('API key saved!');
      } else {
        setApiKeyStatus(data.error || 'Failed to save API key');
      }
    } catch {
      setApiKeyStatus('Failed to save API key (Network error)');
    }
  };


  // Upload handler
  const handleUpload = async (selectedFile: File) => {
    setFile(selectedFile);

    if (!apiKeyInput.trim()) {
      setUploadStatus('Please save your Google API key before uploading.');
      return;
    }

    setUploadStatus('Uploading and indexing...');
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('http://127.0.0.1:5002/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (res.ok && data.session_id) {
        setSessionId(data.session_id);
        setUploadStatus(data.message || 'Upload successful');
        pollProcessingStatus(data.session_id);
      } else {
        setUploadStatus(data.error || 'Upload failed');
      }
    } catch (e) {
      setUploadStatus('Upload failed due to network error.');
    }
  };

  // Fetch token stats
  const fetchTokenStats = async (sid: string) => {
    try {
      const res = await axios.get(`http://127.0.0.1:5002/upload/status/${sid}`);
      // If backend provides a message/status, show it
      if (res.data.message) setUploadStatus(res.data.message);
      else if (res.data.status) setUploadStatus(res.data.status);

      // Ensure all token fields are present for safety
      setTokenStats({
        input_tokens: res.data.input_tokens || 0,
        output_tokens: res.data.output_tokens || 0,
        total_tokens: res.data.total_tokens || 0,
        tokens_used: res.data.tokens_used || 0,
      });
    } catch (err) {
      setTokenStats({
        input_tokens: 0,
        output_tokens: 0,
        total_tokens: 0,
        tokens_used: 0,
      });
    }
  };

  // Fetch stats when sessionId changes
  useEffect(() => {
    if (sessionId) {
      fetchTokenStats(sessionId);
    }
    // Cleanup polling interval on unmount or sessionId change
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [sessionId]);

  // Fetch available jurisdictions on mount
  useEffect(() => {
    const fetchJurisdictions = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:5002/jurisdictions');
        if (Array.isArray(res.data)) setJurisdictions(res.data);
      } catch (e) {
        // ignore
      }
    };
    fetchJurisdictions();
  }, []);

  // When sessionId changes, fetch session details to read current jurisdiction
  useEffect(() => {
    const fetchSessionDetails = async (sid: string) => {
      try {
        const res = await axios.get(`http://127.0.0.1:5002/debug/session/${sid}`);
        const sess = res.data || {};
        if (sess.jurisdiction) setSelectedJurisdiction(sess.jurisdiction);
      } catch (e) {
        // ignore
      }
    };
    if (sessionId) fetchSessionDetails(sessionId);
  }, [sessionId]);


  return (
    <div className="min-h-screen flex flex-col bg-gray-50 font-sans">

      {/* Header (Local Component) */}
      <Header />

      {/* Hero (Local Component) */}
      <Hero handleUpload={handleUpload} file={file} uploadStatus={uploadStatus} apiKeyStatus={apiKeyStatus} />

      {/* Floating Chat Button */}
      {!showChat && <ChatButton onClick={() => setShowChat(true)} />}

      {/* Conditional Chat Panel */}
      {showChat && <ChatPanel sessionId={sessionId} onClose={() => setShowChat(false)} />}

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" id="reports">

        {/* Set API & Status Section */}
        <div className="flex flex-col md:flex-row gap-8 mb-8 w-full justify-center items-stretch">

          {/* Set API Section */}
          <div className="bg-white rounded-lg shadow-lg flex items-center border border-gray-200 w-full md:w-1/2 p-0 min-h-[44px]">
            <form
              className="w-full flex items-center px-4 py-2"
              onSubmit={handleSetApiKey}
            >
              <input
                id="api-key-input"
                type="password"
                className="flex-1 border border-gray-300 rounded-l-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={apiKeyInput}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setApiKeyInput(e.target.value)}
                placeholder="Enter Google API key"
                autoComplete="off"
                style={{ minWidth: 0 }}
              />
              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2 rounded-r-lg shadow transition duration-150 text-sm"
              >
                Save Key
              </button>

              {/* Info button with simpler text display */}
              <button
                type="button"
                className="ml-2 focus:outline-none p-0 bg-transparent hover:bg-transparent active:bg-transparent text-gray-400 hover:text-gray-600 transition"
                title="How to create a Google API key"
                onClick={() => setShowApiInfo(!showApiInfo)}
                style={{ fontSize: '0.95rem', lineHeight: 1, height: 28, width: 28, minWidth: 28, color: 'inherit' }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth={2} fill="none" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 16v-4m0-4h.01" />
                </svg>
              </button>
            </form>
          </div>

          {/* Status/Token Section */}
          <div className="bg-white rounded-lg shadow-lg p-4 border border-gray-200 w-full md:w-1/2">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-base font-semibold text-blue-700">Document Status & Token Usage</h3>
              {sessionId && (
                <button
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition"
                  onClick={() => fetchTokenStats(sessionId)}
                  type="button"
                >
                  Update Stats
                </button>
              )}
            </div>
            <div className="text-sm text-gray-700 space-y-1">
              <div>Status: <span className={`font-semibold ${uploadStatus.includes('completed') ? 'text-green-600' : 'text-orange-500'}`}>{uploadStatus || 'Awaiting upload.'}</span></div>
              {sessionId && (
                <>
                  <div className="border-t border-gray-100 pt-1 mt-1">Total Tokens Used: <span className="font-mono bg-gray-100 rounded px-1">{tokenStats.total_tokens}</span></div>
                  <div className="text-xs text-gray-500">Input: {tokenStats.input_tokens}, Output: {tokenStats.output_tokens}</div>
                </>
              )}
            </div>
          </div>
        </div>
        {/* Jurisdiction Selector (India / UAE etc.) */}
        <div className="flex items-center justify-center mb-6">
          <div className="bg-white rounded-lg shadow-lg p-4 border border-gray-200 w-full max-w-3xl flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Jurisdiction</label>
            <select
              value={selectedJurisdiction || ''}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setSelectedJurisdiction(e.target.value || null)}
              disabled={!sessionId || jurisdictions.length === 0}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <option value="">(None)</option>
              {jurisdictions.map((j) => (
                <option key={j} value={j}>{j.toUpperCase()}</option>
              ))}
            </select>
            <button
              onClick={async () => {
                if (!sessionId) { setJurisdictionMsg('No active session.'); return; }
                if (!selectedJurisdiction) { setJurisdictionMsg('Please select a jurisdiction.'); return; }
                setJurisdictionMsg('Saving...');
                try {
                  const res = await axios.post(`http://127.0.0.1:5002/session/${sessionId}/jurisdiction`, { jurisdiction: selectedJurisdiction });
                  if (res.status === 200) {
                    setJurisdictionMsg('Saved.');
                    // Load rules for the selected jurisdiction
                    try {
                      setRuleLoading(true);
                      const rr = await axios.get(`http://127.0.0.1:5002/rules/${selectedJurisdiction}`);
                      setRuleText(rr.data || '');
                    } catch (e) {
                      setRuleText('Failed to load rules for this jurisdiction.');
                    } finally {
                      setRuleLoading(false);
                    }
                  } else setJurisdictionMsg('Failed to save jurisdiction.');
                } catch (err) {
                  setJurisdictionMsg('Error saving jurisdiction.');
                }
              }}
              disabled={!sessionId}
              className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm"
            >Save</button>
            {jurisdictionMsg && <span className="text-sm text-gray-500 ml-3">{jurisdictionMsg}</span>}
          </div>
        </div>

        {/* Rules panel (shows rules text for selected jurisdiction) */}
        {selectedJurisdiction && (
          <div className="flex items-center justify-center mb-6">
            <div className="bg-white rounded-lg shadow-lg p-4 border border-gray-200 w-full max-w-3xl">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold">Rules: {selectedJurisdiction.toUpperCase()}</h4>
                <div className="flex items-center gap-2">
                  <button
                    onClick={async () => {
                      if (!selectedJurisdiction) return;
                      setRuleLoading(true);
                      try {
                        const rr = await axios.get(`http://127.0.0.1:5002/rules/${selectedJurisdiction}`);
                        setRuleText(rr.data || '');
                      } catch (e) {
                        setRuleText('Failed to load rules.');
                      } finally {
                        setRuleLoading(false);
                      }
                    }}
                    className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded"
                  >Refresh</button>
                </div>
              </div>
              <div className="text-sm text-gray-700 whitespace-pre-wrap max-h-48 overflow-y-auto">
                {ruleLoading ? 'Loading rules...' : (ruleText || 'No rules loaded. Click Refresh or Save to load rules.')}
              </div>
            </div>
          </div>
        )}

        {/* API Info Text Box */}
        {showApiInfo && (
          <div className="bg-blue-50 border-l-4 border-blue-400 text-blue-800 p-4 mb-6 rounded-lg shadow-inner max-w-3xl mx-auto" role="alert">
            <p className="font-bold">Google API Key Information:</p>
            <p className="text-sm">You need a Google API key to power the AI analysis. Get one for free at: <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline hover:text-blue-800">ai.google/dev</a>.</p>
          </div>
        )}


        {/* Formal Button Section */}
        <div className="flex flex-wrap justify-center gap-3 sm:gap-4 mt-10 mb-8">
          <button
            className={`px-4 sm:px-6 py-2 rounded-full font-semibold shadow transition text-sm sm:text-base 
                ${visibleSection === 'comprehensive' ? 'bg-green-600 text-white' : 'bg-white text-green-700 border-2 border-green-500 hover:bg-green-50'}`}
            onClick={() => setVisibleSection('comprehensive')}
          >
            📊 Comprehensive Report
          </button>
          <button
            className={`px-4 sm:px-6 py-2 rounded-full font-semibold shadow transition text-sm sm:text-base 
                ${visibleSection === 'ratios' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
            onClick={() => setVisibleSection('ratios')}
          >
            Financial Ratios
          </button>
          <button
            className={`px-4 sm:px-6 py-2 rounded-full font-semibold shadow transition text-sm sm:text-base
                ${visibleSection === 'balance' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
            onClick={() => setVisibleSection('balance')}
          >
            Compliance Gaps
          </button>
          <button
            className={`px-4 sm:px-6 py-2 rounded-full font-semibold shadow transition text-sm sm:text-base
                ${visibleSection === 'audit' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
            onClick={() => setVisibleSection('audit')}
          >
            Auditor's Report
          </button>
          <button
            className={`px-4 sm:px-6 py-2 rounded-full font-semibold shadow transition text-sm sm:text-base
                ${visibleSection === 'director' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
            onClick={() => setVisibleSection('director')}
          >
            Director's Report
          </button>
          <button
            className={`px-4 sm:px-6 py-2 rounded-full font-semibold shadow transition text-sm sm:text-base
                ${visibleSection === 'summary' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
            onClick={() => setVisibleSection('summary')}
          >
            Summary
          </button>
          <button
            className={`px-4 sm:px-6 py-2 rounded-full font-semibold shadow transition text-sm sm:text-base
                  ${visibleSection === 'peerComparison' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-400 hover:bg-blue-50'}`}
            onClick={() => setVisibleSection('peerComparison')}
          >
            Peer Comparison
          </button>

        </div>

        {/* Report Display Area */}
        <div className="grid grid-cols-1 gap-8 mt-8">

          {/* Comprehensive Report Section */}
          <div
            style={{ display: visibleSection === 'comprehensive' ? 'block' : 'none' }}
            className="bg-white rounded-xl p-6 shadow-2xl border border-green-100"
          >
            <h2 className="text-2xl font-bold text-green-700 mb-4">📊 Comprehensive Financial Analysis</h2>
            <ComprehensiveFinancialReport sessionId={sessionId} />
          </div>

          {/* Financial Ratios Section (Uses original ReportSection for JSON output) */}
          <div
            style={{ display: visibleSection === 'ratios' ? 'block' : 'none' }}
            className="bg-white rounded-xl p-6 shadow-2xl border border-blue-100"
          >
            <h2 className="text-2xl font-bold text-blue-700 mb-4">Financial Ratios & Charts</h2>

            {/* Report Section With Ratio Data */}
            <div className="mb-8">
              <ReportSection
                endpoint="/chat/financial-ratio"
                sessionId={sessionId}
                title="Financial Ratios"
                onDataUpdate={(data) => {
                  // Normalize response: could be wrapped as {response: {...}, balance_sheet_data: [...]}
                  // or direct as {...}
                  const payload = data?.response || data;
                  const ratios = payload?.ratios || payload?.financial_ratios || payload;
                  setLatestRatioData(ratios);
                }}
              />
            </div>

            {/* Dynamic Financial Ratio Chart Visualization */}
            <FinancialCharts
              sessionId={sessionId}
              ratioData={latestRatioData}
              loading={false}
            />
          </div>


          {/* Compliance Gaps Section (Uses HighlightedReportSection - now using structural formatting) */}
          <div
            style={{ display: visibleSection === 'balance' ? 'block' : 'none' }}
            className="bg-white rounded-xl p-6 shadow-2xl border border-blue-100"
          >
            <h2 className="text-2xl font-bold text-blue-700 mb-4">Compliance Gaps Analysis</h2>
            {/* 💡 CHANGE 4: Removed keywords prop */}
            <HighlightedReportSection
              endpoint="/chat/compliance-gap"
              sessionId={sessionId}
              title="Compliance Gaps"
            />
          </div>

          {/* Auditor's Report Section (Uses HighlightedReportSection - now using structural formatting) */}
          <div
            style={{ display: visibleSection === 'audit' ? 'block' : 'none' }}
            className="bg-white rounded-xl p-6 shadow-2xl border border-blue-100"
          >
            <h2 className="text-2xl font-bold text-blue-700 mb-4">Auditor's Report Summary</h2>
            {/* 💡 CHANGE 4: Removed keywords prop */}
            <HighlightedReportSection
              endpoint="/chat/auditor-report"
              sessionId={sessionId}
              title="Auditor's Report"
            />
          </div>

          {/* Director's Report Section (Uses custom component DirectorReport) */}
          <div
            style={{ display: visibleSection === 'director' ? 'block' : 'none' }}
            className="bg-white rounded-xl p-6 shadow-2xl border border-blue-100"
          >
            <h2 className="text-2xl font-bold text-blue-700 mb-4">Director's Report Compliance Check</h2>
            <DirectorReport sessionId={sessionId} title="Director's Report" />
          </div>

          {/* Summary Section (Uses HighlightedReportSection - now using structural formatting) */}
          <div
            style={{ display: visibleSection === 'summary' ? 'block' : 'none' }}
            className="bg-white rounded-xl p-6 shadow-2xl border border-blue-100"
          >
            <h2 className="text-2xl font-bold text-blue-700 mb-4">Overall Document Summary</h2>
            {/* 💡 CHANGE 4: Removed keywords prop */}
            <HighlightedReportSection
              endpoint="/chat/summary"
              sessionId={sessionId}
              title="Summary"
            />
          </div>

          <div
            style={{ display: visibleSection === 'peerComparison' ? 'block' : 'none' }}
            className="bg-white rounded-xl p-6 shadow-2xl border border-blue-100"
          >
            <h2 className="text-2xl font-bold text-blue-700 mb-4">Peer Comparison</h2>
            <PeerComparison />
          </div>


          {/* Testimonials (Local Component) */}
          <Testimonials />
        </div>
      </main>

      {/* Footer (Local Component) */}
      <Footer />
    </div>
  );
};

export default App;