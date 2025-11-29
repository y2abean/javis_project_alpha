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
    try {
      const saved = localStorage.getItem('chat_sessions');
      return saved ? JSON.parse(saved) : [];
    } catch (error) {
      console.error('Failed to load sessions from localStorage:', error);
      return [];
    }
  });

  const [currentSessionId, setCurrentSessionId] = useState(() => {
    try {
      const saved = localStorage.getItem('current_session_id');
      return saved || null;
    } catch (error) {
      console.error('Failed to load currentSessionId from localStorage:', error);
      return null;
    }
  });

  const [isLoading, setIsLoading] = useState(false);

  // Initialize a new chat if no sessions exist
  useEffect(() => {
    if (sessions.length === 0) {
      createNewChat();
    } else {
      // Ensure currentSessionId is valid
      const isValidSession = sessions.some(s => s.id === currentSessionId);
      if (!currentSessionId || !isValidSession) {
        setCurrentSessionId(sessions[0].id);
      }
    }
  }, []);

  // Persist sessions
  useEffect(() => {
    try {
      localStorage.setItem('chat_sessions', JSON.stringify(sessions));
    } catch (error) {
      console.error('Failed to save sessions to localStorage:', error);
      // Optional: Notify user that storage might be full
    }
  }, [sessions]);

  // Persist current session ID
  useEffect(() => {
    try {
      if (currentSessionId) {
        localStorage.setItem('current_session_id', currentSessionId);
      } else {
        localStorage.removeItem('current_session_id');
      }
    } catch (error) {
      console.error('Failed to save currentSessionId to localStorage:', error);
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

  const [userName, setUserName] = useState(() => {
    return localStorage.getItem('user_name') || '';
  });

  // Extract name from message
  const extractNameFromMessage = (text) => {
    // Regex for Korean: "내 이름은 OO야", "나는 OO라고 해", "내 이름은 OO입니다"
    // Using Unicode escapes to avoid encoding issues
    const nameRegex = /(?:\uB0B4\s*\uC774\uB984\uC740|\uB098\uB294)\s*(.*?)(?:(?:\uC774?\uB77C\uACE0\s*\uD574)|(?:\uC774?\uC57C)|(?:\uC785\uB2C8\uB2E4))/i;
    const match = text.match(nameRegex);
    if (match && match[1]) {
      return match[1].trim();
    }
    // Simple check for English: "My name is OO"
    const enMatch = text.match(/My name is (.*)/i);
    if (enMatch && enMatch[1]) {
      return enMatch[1].trim();
    }
    return null;
  };

  const handleSendMessage = async (messageText) => {
    if (!currentSessionId) return;

    // Check for name update
    const detectedName = extractNameFromMessage(messageText);
    if (detectedName) {
      setUserName(detectedName);
      localStorage.setItem('user_name', detectedName);
    } else if (messageText.startsWith('/setname ')) {
      const newName = messageText.replace('/setname ', '').trim();
      if (newName) {
        setUserName(newName);
        localStorage.setItem('user_name', newName);
      }
    }

    const userMessage = { sender: 'user', text: messageText };

    // Add user message
    setSessions(prev => prev.map(session => {
      if (session.id === currentSessionId) {
        const newMessages = [...session.messages, userMessage];
        const newTitle = session.messages.length === 0 ? messageText.slice(0, 30) : session.title;
        return { ...session, messages: newMessages, title: newTitle };
      }
      return session;
    }));

    setIsLoading(true);

    try {
      // Get current session for history
      const currentSession = sessions.find(s => s.id === currentSessionId);
      const history = currentSession ? [...currentSession.messages, userMessage] : [userMessage];

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: messageText,
          history: history,
          userName: userName || (detectedName ? detectedName : undefined) // Send current or just detected name
        }),
      });

      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }

      const data = await response.json();
      const botMessage = { sender: 'bot', text: data.response };

      // Add bot response
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
        text: '\uC8C4\uC1A1\uD569\uB2C8\uB2E4. \uC11C\uBC84\uC5D0 \uC5F0\uACB0\uD560 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4. \uBC31\uC5D4\uB4DC \uC11C\uBC84\uAC00 \uC2E4\uD589 \uC911\uC778\uC9C0 \uD655\uC778\uD574\uC8FC\uC138\uC694.'
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

  const [welcomeMessage, setWelcomeMessage] = useState('');

  useEffect(() => {
    const messages = [
      '\uC548\uB155\uD558\uC138\uC694!', // 안녕하세요!
      '\uBC18\uAC11\uC2B5\uB2C8\uB2E4!', // 반갑습니다!
      '\uBC25\uC740 \uBA39\uC5C8\uB098\uC694?', // 밥은 먹었나요?
      '\uC81C\uAC00 \uD65C\uC57D\uD560 \uC2DC\uAC04\uC774\uAD70\uC694!', // 제가 활약할 시간이군요!
      '\uBB34\uC5C7\uC744 \uB3C4\uC640\uB4DC\uB9B4\uAE4C\uC694?', // 무엇을 도와드릴까요?
      '\uC624\uB298\uB3C4 \uC88B\uC740 \uD558\uB8E8 \uB418\uC138\uC694!', // 오늘도 좋은 하루 되세요!
      '\uAE30\uB2E4\uB9AC\uACE0 \uC788\uC5C8\uC2B5\uB2C8\uB2E4!' // 기다리고 있었습니다!
    ];
    const randomMsg = messages[Math.floor(Math.random() * messages.length)];
    setWelcomeMessage(randomMsg);
  }, []);

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
              <h1>{welcomeMessage}</h1>
              <p>{'NEURON\uACFC \uB300\uD654\uB97C \uC2DC\uC791\uD558\uC138\uC694'}</p>
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
