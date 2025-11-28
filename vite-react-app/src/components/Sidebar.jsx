import React from 'react';
import './Sidebar.css';
import Header from './Header';

function Sidebar({ sessions, currentSessionId, onNewChat, onSelectSession, onDeleteSession }) {
    return (
        <div className="sidebar">
            <Header />
            <button className="new-chat-btn" onClick={onNewChat}>
                + New Chat
            </button>
            <div className="session-list">
                {sessions.map(session => (
                    <div
                        key={session.id}
                        className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                        onClick={() => onSelectSession(session.id)}
                    >
                        <span className="session-title">{session.title || 'New Chat'}</span>
                        {onDeleteSession && (
                            <button
                                className="delete-btn"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDeleteSession(session.id);
                                }}
                            >
                                ×
                            </button>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Sidebar;
