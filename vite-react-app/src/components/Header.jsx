import React from 'react';

function Header() {
    return (
        <header className="header">
            <div className="logo-area">
                <div className="logo-icon">J</div>
                <span>NEURON</span>
            </div>
            <div className="header-actions">
                <button onClick={() => alert('?¤ì • ê¸°ëŠ¥?€ ì¤€ë¹?ì¤‘ìž…?ˆë‹¤.')}>?¤ì •</button>
            </div>
        </header>
    );
}

export default Header;
