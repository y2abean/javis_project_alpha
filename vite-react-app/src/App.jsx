import { useState, useEffect } from 'react';
import './App.css';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';

// Use relative path since frontend and backend are on same domain
const API_URL = import.meta.env.PROD
  ? '/chat'  // Production: same domain
  : 'http://localhost:5000/chat';  // Development: separate ports

function App() {
  const [messages, setMessages] = useState(() => {
    const savedMessages = localStorage.getItem('chat_history');
    return savedMessages ? JSON.parse(savedMessages) : [];
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    localStorage.setItem('chat_history', JSON.stringify(messages));
  }, [messages]);

  const handleSendMessage = async (messageText) => {
    // 사용자 메시지 추가
    const userMessage = { sender: 'user', text: messageText };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: messageText }),
      });

      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }

      const data = await response.json();
      const botMessage = { sender: 'bot', text: data.response };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        sender: 'bot',
        text: '죄송합니다. 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <Header />
      <div className="main-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h1>안녕하세요!</h1>
            <p>NEURON과 대화를 시작하세요</p>
          </div>
        ) : (
          <ChatWindow messages={messages} />
        )}
        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}

export default App;
