import React, { useState, useRef } from 'react';
import './BalanceSheetChecker.css';

const ENTITY_OPTIONS = [
  "One Person Company",
  "Public Listed Company",
  "Unlisted Limited Company",
  "Private Limited Company",
  "Others"
];

const Small_company = `
Analysis of Small Company:-
 (1) A public company will never be a small company. 
(2) A Private company should have a maximum of :-
 (a) Paid up capital of Rs 50 Lakhs
 (b) Turnover of Rs 2 Crores.
 (3) Holding and Subsidiary will always be out of the picture of small companies.
`;
const CSR = `
Analysis of Corporate Social Responsibility (CSR) and also check/calculate Net worth (total assets - total liabilities), turnover and net profit, then only provide further details:- 
CSR is applicable to companies that, in the preceding financial year, had:
 (1) Net worth > ₹500 crores, or
 (2) Turnover > ₹1000 crores, or
 (3) Net profit > ₹5 crores.
If a company does not meet any of these criteria, CSR is not applicable.
`;

const ACCOUNTING_STANDARDS = [
  "AS 1 Disclosure of Accounting Policies",
  "AS 2 Valuation of Inventories",
  "AS 3 Cash Flow Statements: This standard is not applicable to One Person Companies, Small Company("+Small_company+"), and Dormant company.",
  "AS 4 Contingencies and Events Occurring After the Balance Sheet Date",
  "AS 5 Net Profit or Loss for the Period, Prior Period Items and Changes in Accounting Policies",
  "AS 7 Construction Contracts",
  "AS 9 Revenue Recognition",
  "AS 10 Property, Plant and Equipment",
  "AS 11 The Effects of Changes in Foreign Exchange Rates",
  "AS 12 Accounting for Government Grants",
  "AS 13 Accounting for Investments",
  "AS 14 Accounting for Amalgamations",
  "AS 15 Employee Benefits",
  "AS 16 Borrowing Costs",
  "AS 17 Segment Reporting",
  "AS 18 Related Party Disclosures",
  "AS 19 Leases",
  "AS 20 Earnings Per Share",
  "AS 21 Consolidated Financial Statements",
  "AS 22 Accounting for Taxes on Income",
  "AS 23 Accounting for Investments in Associates in Consolidated Financial Statements",
  "AS 24 Discontinuing Operations",
  "AS 25 Interim Financial Reporting",
  "AS 26 Intangible Assets",
  "AS 27 Financial Reporting of Interests in Joint Ventures",
  "AS 28 Impairment of Assets",
  "AS 29 Provisions, Contingent Liabilities and Contingent Assets",
  "Corporate Social Responsibility: "+CSR+" ",
  "MSME: Disclosure of principal amount and interest due to Micro, Small and Medium Enterprises under the MSMED Act, 2006"
];

const GEMINI_API_KEY = 'AIzaSyAgjjIB1JKQL0L9wIKUb4XBCUYtXeiomjc';

const BalanceSheetChecker = ({ recentFileName }: { recentFileName: string | null }) => {
  const [markdownContent, setMarkdownContent] = useState('');
  const [entityType, setEntityType] = useState('');
  const [results, setResults] = useState<{ result: string; [key: string]: any }[]>([]);
  const [showPassingRules, setShowPassingRules] = useState(false);
  const [summary, setSummary] = useState('');
  const [message, setMessage] = useState('');
  const [chatMessages, setChatMessages] = useState<{ user: string; text: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [showEntityModal, setShowEntityModal] = useState(false);
  const chatInputRef = useRef<HTMLInputElement>(null);

  // Utility: Show temporary message
  const showMessage = (msg: string) => {
    setMessage(msg);
    setTimeout(() => setMessage(''), 3000);
  };

  // Fetch markdown file
  const fetchMarkdownFile = async () => {
    if (!recentFileName) {
      showMessage('No file selected. Please upload a PDF first.');
      return;
    }
    const markdownFileName = recentFileName.replace('.pdf', '.md');
    const markdownFilePath = `./saved_markdowns/${markdownFileName}`;
    try {
      const response = await fetch(markdownFilePath);
      if (!response.ok) throw new Error(`Failed to fetch the file: ${markdownFilePath}`);
      const text = await response.text();
      setMarkdownContent(text);
      showMessage('Select Entity Type and click Analyse to proceed..');
    } catch (error) {
      showMessage('Error loading file.');
    }
  };

  // Clean markdown content
  const cleanMarkdownContent = (content: string) => content.replace(/<\/?[^>]+(>|$)/g, '');

  // Analyze balance sheet
  const analyzeBalanceSheet = async () => {
    if (!entityType || !markdownContent) {
      showMessage('Missing entity type or markdown content.');
      return;
    }
    const cleanedContent = cleanMarkdownContent(markdownContent);
    setResults([]);
    setSummary('');
    setIsLoading(true);

    // Improved prompt for more informative and explicit results
    const prompt = `You are an expert financial analyst. Analyze the following balance sheet data for a ${entityType} and check ONLY the following Accounting Standards (in this order):

${ACCOUNTING_STANDARDS.join('\n')}

For each standard, output a JSON object with these fields:
- "standard": Name of the standard (always fill this)
- "section": Section or clause (if not available, write "General")
- "rule": The specific rule being checked (always fill this)
- "result": "PASS", "FAIL", or "NA"
- "expected": What is expected for compliance
- "actual": What is found in the markdown (or "Not found")
- "message": A brief explanation. If "NA", explain why (e.g., "Data not found in the markdown" or "Not applicable to this entity type"). If "FAIL", explain what is missing or incorrect.

If information is missing, set "result" to "NA" and explain in "message".

Balance Sheet Data (in Markdown format):
${cleanedContent}

Provide your response as a JSON array of rule checks with "standard", "section", "rule", "result" (PASS/FAIL/NA), "expected", "actual", "message".`;

    const body = { contents: [{ parts: [{ text: prompt }] }] };

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
      showMessage('Failed to analyze the balance sheet. Please check the file format or try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Chat with AI
  const sendChat = async () => {
    const input = chatInputRef.current?.value.trim();
    if (!input || !markdownContent) return;

    const prompt = `You are an expert financial analyst. Provide response in breif and informative. Analyze the following balance sheet data and answer: ${input}

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

      setChatMessages((msgs) => [...msgs, { user: 'You', text: input }, { user: 'Answer', text: reply }]);
      if (chatInputRef.current) chatInputRef.current.value = '';
    } catch {
      showMessage('Error sending message to Server.');
    }
  };

  // --- Render ---
  return (
    <div>
      {/* File Loader */}
      <div className="mb-8 text-center">
        <br />
        <button
          onClick={() => setShowEntityModal(true)}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Select Entity
        </button>
      </div>

      {/* Entity Selection Modal */}
      {showEntityModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-xs">
            <h2 className="text-lg font-semibold mb-4 text-gray-800 text-center">Select Entity Type</h2>
            <ul className="space-y-3">
              {ENTITY_OPTIONS.map((option) => (
                <li key={option}>
                  <button
                    className={`w-full py-2 px-4 rounded text-left border ${
                      entityType === option
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-gray-100 hover:bg-blue-50 border-gray-300 text-gray-800'
                    }`}
                    onClick={async () => {
                      setEntityType(option);
                      setShowEntityModal(false);
                      await fetchMarkdownFile();
                    }}
                  >
                    {option}
                  </button>
                </li>
              ))}
            </ul>
            <button
              className="mt-5 w-full py-2 px-4 rounded bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold"
              onClick={() => setShowEntityModal(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Entity Type Selector & Analyze */}
      {markdownContent && entityType && (
        <div className="mb-8 text-center">
          <h2 className="font-semibold text-gray-800 mb-4">Entity Type: <span className="text-blue-700">{entityType}</span></h2>
          <button
            onClick={analyzeBalanceSheet}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4"
            disabled={isLoading}
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
            ) : 'Analyse'}
          </button>
        </div>
      )}

      {/* Results Table */}
      {results.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Analysis Results</h2>
          <button
            onClick={() => setShowPassingRules((prev) => !prev)}
            className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mb-4"
          >
            {showPassingRules ? 'Hide Passing Rules' : 'Show Passing Rules'}
          </button>
          <div className="w-full overflow-x-auto max-h-[500px] overflow-y-auto rounded shadow border border-gray-200">
            <table className="min-w-[900px] w-full border-collapse text-sm">
              <thead className="bg-blue-50 sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-2 border-b font-semibold text-gray-800 text-left">Standard</th>
                  <th className="px-4 py-2 border-b font-semibold text-gray-800 text-left">Section</th>
                  <th className="px-4 py-2 border-b font-semibold text-gray-800 text-left">Rule</th>
                  <th className="px-4 py-2 border-b font-semibold text-gray-800 text-left">Result</th>
                  <th className="px-4 py-2 border-b font-semibold text-gray-800 text-left">Expected</th>
                  <th className="px-4 py-2 border-b font-semibold text-gray-800 text-left">Actual</th>
                  <th className="px-4 py-2 border-b font-semibold text-gray-800 text-left">Message</th>
                </tr>
              </thead>
              <tbody>
                {results
                  .filter((r) => showPassingRules || r.result === 'FAIL')
                  .map((item, idx) => (
                    <tr key={idx} className="hover:bg-blue-50 even:bg-gray-50">
                      <td className="px-4 py-2 border-b">{item.standard}</td>
                      <td className="px-4 py-2 border-b">{item.section}</td>
                      <td className="px-4 py-2 border-b">{item.rule}</td>
                      <td className={`px-4 py-2 border-b font-semibold ${item.result === 'FAIL' ? 'text-red-600' : 'text-green-700'}`}>{item.result}</td>
                      <td className="px-4 py-2 border-b">{item.expected}</td>
                      <td className="px-4 py-2 border-b">{item.actual}</td>
                      <td className="px-4 py-2 border-b">{item.message}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-gray-700">{summary}</p>
        </div>
      )}

      {/* Chat Floating Button and Chat Window */}
      <div>
        {/* Floating Chat Button */}
        {!isChatOpen && (
          <button
            onClick={() => setIsChatOpen(true)}
            className="fixed bottom-6 right-6 z-50 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg px-6 py-3 flex items-center gap-2 font-semibold text-base"
            style={{ boxShadow: '0 4px 24px rgba(80,80,180,0.15)' }}
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.77 9.77 0 01-4-.8L3 20l.8-4A8.96 8.96 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            Chat
          </button>
        )}

        {/* Chat Window */}
        {isChatOpen && (
          <div className="fixed bottom-6 right-6 z-50 w-96 max-w-full bg-white border border-gray-300 rounded-lg shadow-lg flex flex-col"
            style={{ minHeight: 340, maxHeight: 500 }}>
            <div className="flex items-center justify-between px-4 py-2 border-b bg-indigo-600 rounded-t-lg">
              <span className="text-white font-semibold">Ask about this Balance Sheet</span>
              <button
                onClick={() => setIsChatOpen(false)}
                className="text-white hover:text-gray-200 text-xl font-bold"
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <div className="chat-container flex-1 border-0 rounded-b-md p-4 bg-gray-50 flex flex-col h-64 overflow-y-auto mb-2">
              {chatMessages.length === 0 && (
                <div className="text-gray-400 text-center mt-8">No messages yet. Ask your question!</div>
              )}
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`mb-2 ${msg.user === 'You' ? 'text-right' : 'text-left'}`}>
                  <p className="text-xs font-bold text-gray-500">{msg.user}</p>
                  <div className={`inline-block px-3 py-2 rounded-lg ${msg.user === 'You' ? 'bg-indigo-100 text-indigo-900' : 'bg-gray-200 text-gray-800'}`}>
                    <p className="text-sm">{msg.text}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex space-x-2 px-4 pb-4">
              <input
                ref={chatInputRef}
                type="text"
                className="border border-gray-300 p-2 rounded-md flex-1 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                placeholder="Ask question in relation to uploaded financial statements"
                onKeyDown={e => { if (e.key === 'Enter') sendChat(); }}
              />
              <button
                onClick={sendChat}
                className="bg-indigo-500 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded"
              >
                Send
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Floating Message */}
      {message && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-green-100 text-green-700 px-4 py-2 rounded shadow-md z-50">
          {message}
        </div>
      )}
    </div>
  );
};

export default BalanceSheetChecker;
