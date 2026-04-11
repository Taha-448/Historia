import React, { useEffect, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

function PatientPortal({ messages, setMessages, input, setInput }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: 'User', text: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');

    try {
      console.log(`Sending message to ${API_BASE_URL}/chat/web...`);
      const response = await axios.post(`${API_BASE_URL}/chat/web`, { text: input });
      console.log("Received response:", response.data);
      if (response.data && response.data.response) {
        setMessages([...newMessages, { sender: 'AI', text: response.data.response }]);
      } else {
        throw new Error("Invalid response format from server");
      }
    } catch (error) {
      console.error("Error sending message:", error);
      const errorText = error.response?.data?.response || "Server connection failed. Please ensure the backend is running.";
      setMessages([...newMessages, { sender: 'AI', text: errorText }]);
    }
  };

  return (
    <div className="container">
      <h2>🏥 Patient Interview Portal</h2>
      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={`message-container ${msg.sender === 'User' ? 'user' : 'ai'}`}>
            <span className="message-bubble">
              {msg.text}
            </span>
          </div>
        ))}
        {/* Dummy div to anchor the scroll */}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your symptoms..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default PatientPortal;
