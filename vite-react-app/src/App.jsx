import { useState, useEffect } from 'react';
import './App.css';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import Sidebar from './components/Sidebar';

// Use Render backend for production, localhost for development
const API_URL = import.meta.env.DEV
  ? 'http://localhost:5000/chat'
  : 'https://javis-project-alpha.onrender.com/chat';

function App() {
  // Session state: array of { id, title, messages, date }
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem('chat_sessions');
    return saved ? JSON.parse(saved) : [];
  });

  const [currentSessionId, setCurrentSessionId] = useState(() => {
    const saved = localStorage.getItem('current_session_id');
    return saved || null;
  });

  const [isLoading, setIsLoading] = useState(false);

  // Initialize a new chat if no sessions exist
  useEffect(() => {
    if (sessions.length === 0) {
      createNewChat();
    } else if (!currentSessionId) {
      setCurrentSessionId(sessions[0].id);
    }
  }, []);

  // Persist sessions
  useEffect(() => {
    localStorage.setItem('chat_sessions', JSON.stringify(sessions));
  }, [sessions]);

  // Persist current session ID
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('current_session_id', currentSessionId);
    }
  }, [currentSessionId]);

  const createNewChat = () => {
    const newSession = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      date: new Date().toISOString()
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  };

  const deleteSession = (id) => {
    setSessions(prev => {
      const newSessions = prev.filter(s => s.id !== id);
      if (newSessions.length === 0) {
        setTimeout(createNewChat, 0);
        return [];
      }
      if (id === currentSessionId) {
        setCurrentSessionId(newSessions[0].id);
      }
      return newSessions;
    });
  };

  const getCurrentMessages = () => {
    const session = sessions.find(s => s.id === currentSessionId);
    return session ? session.messages : [];
  };

  const handleSendMessage = async (messageText) => {
    if (!currentSessionId) return;

    const userMessage = { sender: 'user', text: messageText };

    let updatedSessions = [];
    setSessions(prev => {
      updatedSessions = prev.map(session => {
        if (session.id === currentSessionId) {
          const newMessages = [...session.messages, userMessage];
          const newTitle = session.messages.length === 0 ? messageText.slice(0, 30) : session.title;
          return { ...session, messages: newMessages, title: newTitle };
        }
        return session;
      });
      return updatedSessions;
    });

    setIsLoading(true);

    try {
      const currentSession = updatedSessions.find(s => s.id === currentSessionId);
      const history = currentSession ? currentSession.messages : [userMessage];

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: messageText, history: history }),
      });

      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }

      const data = await response.json();
      const botMessage = { sender: 'bot', text: data.response };

      setSessions(prev => prev.map(session => {
        if (session.id === currentSessionId) {
          return { ...session, messages: [...session.messages, botMessage] };
        }
        return session;
      }));

    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        sender: 'bot',
        text: '죄송합니다. 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.'
      };
      setSessions(prev => prev.map(session => {
        if (session.id === currentSessionId) {
          return { ...session, messages: [...session.messages, errorMessage] };
        }
        return session;
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const currentMessages = getCurrentMessages();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className={`app ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      <div className={`sidebar-wrapper ${isSidebarOpen ? 'open' : 'closed'}`}>
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onNewChat={createNewChat}
          onSelectSession={setCurrentSessionId}
          onDeleteSession={deleteSession}
        />
      </div>
      <div className="main-content">
        <div className="top-bar">
          <button className="toggle-sidebar-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)} title={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}>
            <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="9" y1="3" x2="9" y2="21"></line>
            </svg>
          </button>
        </div>
        <div className="chat-container">
          {currentMessages.length === 0 ? (
            <div className="welcome-message">
              <h1>안녕하세요!</h1>
              <p>NEURON과 대화를 시작하세요</p>
            </div>
          ) : (
            <ChatWindow messages={currentMessages} />
          )}
          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
}

export default App;
