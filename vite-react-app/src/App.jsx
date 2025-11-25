import { useState } from 'react'
import './App.css'
import Header from './components/Header'
import ChatWindow from './components/ChatWindow'
import ChatInput from './components/ChatInput'

function App() {
  const [messages, setMessages] = useState([
    { sender: 'assistant', text: '?ˆë…•?˜ì„¸?? ë¬´ì—‡???„ì??œë¦´ê¹Œìš”?' }
  ]);

  const handleSend = async (text) => {
    // Add user message
    setMessages(prev => [...prev, { sender: 'user', text }]);

    try {
      const response = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: text }),
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: data.response
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: `?¤ë¥˜ê°€ ë°œìƒ?ˆìŠµ?ˆë‹¤: ${error.message}`
      }]);
    }
  };

  return (
    <div className="app-container">
      <Header />
      <ChatWindow messages={messages} />
      <ChatInput onSend={handleSend} />
    </div>
  )
}

export default App
