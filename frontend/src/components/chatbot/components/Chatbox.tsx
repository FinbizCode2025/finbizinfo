import { useState } from 'react';
import './Chatbox.css';

function Chatbox({ darkMode }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [chatVisible, setChatVisible] = useState(false);

  const handleQueryChange = (event) => {
    setQuery(event.target.value);
  };

  const handleSendMessage = async () => {
    if (!query.trim()) return;

    const userMessage = { sender: 'user', text: query };
    setMessages((prevMessages) => [...prevMessages, userMessage]);

    setLoading(true);
    try {
      const res = await fetch('http://162.55.51.80:5000/chat', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      const botMessage = { sender: 'bot', text: data.response || 'Sorry, I couldn\'t generate a response.' };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.log(error);
      const botMessage = { sender: 'bot', text: 'Error: Unable to connect to the backend.' };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    }
    setLoading(false);
    setQuery('');
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      if (event.shiftKey) {
        setQuery(query + '\n');
      } else {
        handleSendMessage();
      }
      event.preventDefault();
    }
  };

  const toggleChatVisibility = () => {
    setChatVisible((prev) => !prev);
  };

  return (
    <>
      {!chatVisible && (
        <button className="chat-button" onClick={toggleChatVisibility}>
          <span className="chat-icon">💬</span>
        </button>
      )}

      {chatVisible && (
        <div className={`chatbox-container ${darkMode ? 'dark' : 'light'}`}>
          <div className="chatbox-header">
            <div className="chat-title">Chatbot</div>
            <button className="close-chat-button" onClick={toggleChatVisibility}>✖</button>
          </div>

          <div className="chatbox">
            <div className="chatbox-messages">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
                >
                  <div className={`message-bubble ${message.sender === 'user' ? 'user-bubble' : 'bot-bubble'}`}>
                    {message.text}
                  </div>
                </div>
              ))}
              {loading && <div className="message bot-message loading">...</div>}
            </div>
          </div>

          <div className="chatbox-input-container">
            <textarea
              value={query}
              onChange={handleQueryChange}
              onKeyDown={handleKeyPress}
              placeholder="Type a message..."
              rows="2"
              className="chat-input"
            />
            <button className="send-button" onClick={handleSendMessage}>
              <span className="send-icon">➤</span>
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default Chatbox;