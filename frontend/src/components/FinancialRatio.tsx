import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './FinancialRatio.css';

const Chatbot = ({ recentFileName }: { recentFileName: string | null }) => {
  const [messages, setMessages] = useState<{ text: string; sender: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (recentFileName) {
      const markdownFileName = recentFileName.replace('.pdf', '.md'); // Replace .pdf with .md
      const systemMessage = { text: `Using markdown file: ${markdownFileName} from saved_markdowns.`, sender: 'system' };
      setMessages([systemMessage]);
    }
  }, [recentFileName]);

  const handleAnalyzeMarkdown = async () => {
    if (!recentFileName) {
      alert('No markdown file available for analysis. Please upload a PDF first.');
      return;
    }

    // Clear previous messages before starting a new analysis
    setMessages([]);

    const markdownFileName = recentFileName.replace('.pdf', '.md'); // Replace .pdf with .md
    const markdownFilePath = `http://82.180.145.47:5002/saved_markdowns/${markdownFileName}`; // Full path to the markdown file

    setIsLoading(true);
    const userMessage = { text: `Analyzing financial ratios for: ${markdownFileName}`, sender: 'user' };
    setMessages((prev) => [...prev, userMessage]);

    try {
      console.log(`Fetching markdown file from: ${markdownFilePath}`);
      const fileResponse = await fetch(markdownFilePath);

      if (!fileResponse.ok) {
        throw new Error(`Failed to fetch the markdown file: ${markdownFilePath} (Status: ${fileResponse.status})`);
      }

      const markdownBlob = await fileResponse.blob();
      const formData = new FormData();
      formData.append('markdown', markdownBlob, markdownFileName);

      const backendUrl = 'http://82.180.145.47:5002/analyze_pdf_ratios';
      console.log(`Sending analysis request to: ${backendUrl}`);

      const response = await fetch(backendUrl, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.response) {
        console.log('Analysis successful:', data.response);
        setMessages((prev) => [
          ...prev,
          { text: data.response, sender: 'bot' },
        ]);
      } else {
        const errorMessage = data.error || `Analysis failed with status: ${response.status}`;
        console.error('Analysis error:', errorMessage);
        setMessages((prev) => [
          ...prev,
          { text: `Error: ${errorMessage}`, sender: 'bot' },
        ]);
      }
    } catch (error) {
      console.error('Fetch error:', error);
      setMessages((prev) => [
        ...prev,
        { text: `Error: Could not connect to the analysis server. ${error instanceof Error ? error.message : 'Unknown error'}`, sender: 'bot' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="financial_statement">
        <div>
          <h1 className="text-3xl font-bold text-center text-black-600 mb-8">Calculate Financial Ratios</h1>
          <div className="mt-4">
            {recentFileName && (
              <p id="file-name" className="text-gray-700 mt-2">
                <strong>Current File:</strong> {recentFileName.replace('.pdf', '.md')}
              </p>
            )}
          </div>
          <br />
          <button
            onClick={handleAnalyzeMarkdown}
            disabled={isLoading || !recentFileName}
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
          >
            {isLoading ? 'Analysing...' : 'Analyse Financial Ratios'}
          </button>
        </div>

        <div className="response">
          {isLoading && <p className="text-blue-500">Loading...</p>}
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              {msg.sender === 'bot' ? (
                <div className="bot-message-markdown">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              ) : (
                <pre style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</pre>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
