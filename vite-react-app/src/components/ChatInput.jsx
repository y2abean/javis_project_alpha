import React, { useState } from 'react';
import './ChatInput.css';

function ChatInput({ onSendMessage, disabled }) {
    const [message, setMessage] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim() && !disabled) {
            onSendMessage(message);
            setMessage('');
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <form className="chat-input" onSubmit={handleSubmit}>
            <div className="input-container">
                <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="NEURON에게 메시지 보내기..."
                    rows="3"
                    disabled={disabled}
                />
                <button type="submit" disabled={disabled}>
                    {disabled ? '전송 중...' : '전송'}
                </button>
            </div>
        </form>
    );
}

export default ChatInput;
