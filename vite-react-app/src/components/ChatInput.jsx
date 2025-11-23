import React, { useState } from 'react';

function ChatInput({ onSend }) {
    const [input, setInput] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.trim()) {
            onSend(input);
            setInput('');
        }
    };

    return (
        <div className="input-area">
            <form className="input-form" onSubmit={handleSubmit}>
                <input
                    type="text"
                    className="chat-input"
                    placeholder="Jarvis에게 메시지 보내기..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                />
                <button type="submit" className="send-btn" disabled={!input.trim()}>
                    전송
                </button>
            </form>
        </div>
    );
}

export default ChatInput;
