import React, { useState, useRef } from 'react';
import './BalanceSheetChecker.css'; // Add this for custom CSS styles

const BalanceSheetChecker = ({ recentFileName }: { recentFileName: string | null }) => {
  const [markdownContent, setMarkdownContent] = useState('');
  const [entityType, setEntityType] = useState('');
  const [results, setResults] = useState<{ result: string; [key: string]: any }[]>([]);
  const [showPassingRules, setShowPassingRules] = useState(false);
  const [summary, setSummary] = useState('');
  const [message, setMessage] = useState('');
  const [chatMessages, setChatMessages] = useState<{ user: string; text: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false); // State for loading spinner
  const chatInputRef = useRef<HTMLInputElement>(null);
  const GEMINI_API_KEY = 'AIzaSyAgjjIB1JKQL0L9wIKUb4XBCUYtXeiomjc';

  const showMessage = (msg: string) => {
    setMessage(msg);
    setTimeout(() => setMessage(''), 3000);
  };

  const fetchMarkdownFile = async () => {
    if (!recentFileName) {
      showMessage('No file selected. Please upload a PDF first.');
      return;
    }

    const markdownFileName = recentFileName.replace('.pdf', '.md'); // Replace .pdf with .md
    const markdownFilePath = `./saved_markdowns/${markdownFileName}`; // Path to the markdown file

    try {
      const response = await fetch(markdownFilePath);
      if (!response.ok) {
        throw new Error(`Failed to fetch the file: ${markdownFilePath}`);
      }
      const text = await response.text();
      setMarkdownContent(text);
      showMessage('Select Entity Type and click Analyse to proceed..');
    } catch (error) {
      console.error(error);
      showMessage('Error loading file.');
    }
  };

  const analyzeBalanceSheet = async () => {
    if (!entityType || !markdownContent) {
      showMessage('Missing entity type or markdown content.');
      return;
    }

    // Clear previous results before starting a new analysis
    setResults([]);
    setSummary('');
    setIsLoading(true); // Show loading spinner

    const prompt = `You are an expert financial analyst. Analyze the following balance sheet data for a ${entityType} and identify if it follows the accounting standards.

Balance Sheet Data:
${markdownContent}

Provide your response as a JSON array of rule checks with "standard", "section", "rule", "result" (PASS/FAIL), "expected", "actual", "message".`;

    const body = {
      contents: [{ parts: [{ text: prompt }] }],
    };

    try {
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        }
      );
      const data = await res.json();
      let text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
      text = text.replace(/```json\n?|\n?```/g, '');
      const parsed = JSON.parse(text);
      setResults(parsed);

      const failCount = parsed.filter((r: any) => r.result === 'FAIL').length;
      const passCount = parsed.length - failCount;
      setSummary(`${passCount} rules passed, ${failCount} rules failed.`);
    } catch (err) {
      console.error(err);
      showMessage('Failed to analyze the balance sheet.');
    } finally {
      setIsLoading(false); // Hide loading spinner
    }
  };

  const sendChat = async () => {
    const input = chatInputRef.current?.value.trim();
    if (!input || !markdownContent) return;

    const prompt = `You are an expert financial analyst. Analyze the following balance sheet data and answer: ${input}

Data:
${markdownContent}`;

    try {
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
        }
      );
      const data = await res.json();
      let reply = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
      reply = reply.replace(/```json\n?|\n?```/g, '');

      setChatMessages((msgs) => [...msgs, { user: 'You', text: input }, { user: 'Gemini', text: reply }]);
      if (chatInputRef.current) chatInputRef.current.value = '';
    } catch {
      showMessage('Error sending message to Gemini.');
    }
  };

  return (
    <div className="container mx-auto p-8 bg-white rounded-lg shadow-md">
      <h1 className="text-3xl font-bold text-center text-black-600 mb-8">Analyse Compliance Gaps</h1>
      <div className="mb-8 text-center">
        {recentFileName && (
          <p id="file-name" className="text-gray-700 mt-2">
            <strong>Current File:</strong> {recentFileName.replace('.pdf', '.md')}
          </p>
        )}
        <br />
        <button
          onClick={fetchMarkdownFile}
          className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
        >
          Load Markdown
        </button>
      </div>

      {markdownContent && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Select Entity Type</h2>
          <select
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            className="border p-2 rounded-md w-full"
          >
            <option value="">Select Entity Type</option>
            <option value="Proprietorship">Proprietorship</option>
            <option value="Ltd Company">Limited Company</option>
            <option value="NPO">Non-Profit Organization</option>
            <option value="Partnership">Partnership</option>
            <option value="LLP">LLP</option>
          </select>
          <button
            onClick={analyzeBalanceSheet}
            className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded mt-4"
            disabled={isLoading} // Disable button while loading
          >
            {isLoading ? 'Analyzing...' : 'Analyse'}
          </button>
          {isLoading && (
            <div className="loading-ring mt-4 mx-auto"></div> // Add loading ring
          )}
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Analysis Results</h2>
          <button
            onClick={() => setShowPassingRules((prev) => !prev)}
            className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mb-4"
          >
            {showPassingRules ? 'Hide Passing Rules' : 'Show Passing Rules'}
          </button>
          <table className="w-full border-collapse border rounded shadow">
            <thead className="bg-gray-100">
              <tr>
                <th>Standard</th>
                <th>Section</th>
                <th>Rule</th>
                <th>Result</th>
                <th>Expected</th>
                <th>Actual</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {results
                .filter((r) => showPassingRules || r.result === 'FAIL')
                .map((item, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td>{item.standard}</td>
                    <td>{item.section}</td>
                    <td>{item.rule}</td>
                    <td className={item.result === 'FAIL' ? 'text-red-600 font-semibold' : ''}>{item.result}</td>
                    <td>{item.expected}</td>
                    <td>{item.actual}</td>
                    <td>{item.message}</td>
                  </tr>
                ))}
            </tbody>
          </table>
          <p className="mt-4 text-gray-700">{summary}</p>
        </div>
      )}

      <div className="mt-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Response here:</h2>
        <div className="chat-container border rounded-md p-4 bg-gray-50 flex flex-col h-[200px] overflow-y-auto mb-4">
          {chatMessages.map((msg, idx) => (
            <div key={idx} className={msg.user === 'You' ? 'text-right' : 'text-left'}>
              <p className="text-sm font-bold">{msg.user}</p>
              <p className="text-gray-700">{msg.text}</p>
            </div>
          ))}
        </div>
        <div className="flex space-x-2">
          <input
            ref={chatInputRef}
            type="text"
            className="border p-2 rounded-md flex-1"
            placeholder="Ask question in relation to uploaded financial statements"
          />
          <button
            onClick={sendChat}
            className="bg-indigo-500 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded"
          >
            Send
          </button>
        </div>
      </div>

      {message && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-green-100 text-green-700 px-4 py-2 rounded shadow-md z-50">
          {message}
        </div>
      )}
    </div>
  );
};

export default BalanceSheetChecker;
