import React from 'react';

function Header() {
    return (
        <header className="header">
            <div className="logo-area">
                <div className="logo-icon">J</div>
                <span>JARVIS</span>
            </div>
            <div className="header-actions">
                <button onClick={() => alert('설정 기능은 준비 중입니다.')}>설정</button>
            </div>
        </header>
    );
}

export default Header;
