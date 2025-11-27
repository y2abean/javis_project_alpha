import React, { useEffect, useRef } from 'react';
import './ChatWindow.css';

import ReactMarkdown from 'react-markdown';

function ChatWindow({ messages }) {
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    return (
        <div className="chat-window">
            {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.sender}`}>
                    <div className="message-header">
                        {msg.sender === 'user' ? 'You' : 'NEURON'}
                    </div>
                    <div className="message-content">
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                </div>
            ))}
            <div ref={messagesEndRef} />
        </div>
    );
}

export default ChatWindow;
