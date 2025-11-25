import React, { useState } from 'react';
import './ChatInput.css';

function ChatInput({ onSendMessage }) {
    const [message, setMessage] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim()) {
            onSendMessage(message);
            setMessage('');
        }
    };

    return (
        <form className="chat-input" onSubmit={handleSubmit}>
            <div className="input-container">
                <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="NEURON에게 메시지 보내기..."
                    rows="3"
                />
                <button type="submit">전송</button>
            </div>
        </form>
    );
}

export default ChatInput;
