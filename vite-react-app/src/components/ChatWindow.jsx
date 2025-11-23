import React, { useEffect, useRef } from 'react';

function ChatWindow({ messages }) {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="chat-window">
            {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.sender}`}>
                    <div className="message-sender">
                        {msg.sender === 'user' ? 'You' : 'Jarvis'}
                    </div>
                    <div className="message-bubble">
                        {msg.text}
                    </div>
                </div>
            ))}
            <div ref={bottomRef} />
        </div>
    );
}

export default ChatWindow;
