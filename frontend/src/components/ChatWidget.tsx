import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface ChatWidgetProps {
  sessionId: string | null;
}

const ChatWidget: React.FC<ChatWidgetProps> = ({ sessionId }) => {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState<{ user: string; bot: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!message.trim()) return;
    if (!sessionId) {
      alert('Please upload a file before starting chat.');
      return;
    }

    setLoading(true);
    const userMessage = message;
    setMessage('');

    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('query', userMessage);

      const res = await fetch('http://127.0.0.1:5002/chat/message', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      const botMessage = data.response || data.error || 'No response.';

      setChatLog((prev) => [...prev, { user: userMessage, bot: botMessage }]);
    } catch (e) {
      setChatLog((prev) => [...prev, { user: userMessage, bot: '❌ Error reaching server.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-11 right-11 z-50">
      {open ? (
        <div className="bg-white border border-gray-300 shadow-xl rounded-xl w-96 max-h-[75vh] flex flex-col overflow-hidden">
          <div className="bg-blue-600 text-white px-4 py-3 flex justify-between items-center">
            <span className="font-semibold text-lg">AI Chat Assistant</span>
            <button onClick={() => setOpen(false)} className="text-white hover:text-gray-200 text-sm">✖</button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 text-sm leading-relaxed font-sans">
            {chatLog.map((msg, idx) => (
              <div key={idx} className="space-y-2">
                <div className="text-right">
                  <div className="inline-block bg-blue-100 text-blue-900 px-4 py-2 rounded-lg shadow-sm max-w-[85%] text-left whitespace-pre-line">
                    <strong>You:</strong> <ReactMarkdown>{msg.user}</ReactMarkdown>
                  </div>
                </div>
                <div className="text-left">
                  <div className="inline-block bg-gray-200 text-gray-900 px-4 py-2 rounded-lg shadow-sm max-w-[85%] whitespace-pre-line">
                    <strong>Bot:</strong> <ReactMarkdown>{msg.bot}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="p-3 bg-white border-t border-gray-200 flex gap-2">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask something..."
              className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
            />
            <button
              onClick={handleSend}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm shadow"
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="bg-blue-500 text-white w-25 h-25 m-10 rounded-full shadow-lg hover:bg-blue-700 text-2xl flex items-center justify-center"
        >
          💬
        </button>
      )}
    </div>
  );
};

export default ChatWidget;
