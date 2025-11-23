import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          카운트: {count}
        </button>
        <p>
          <code>src/App.jsx</code> 파일을 수정하고 저장하여 HMR을 테스트해보세요.
        </p>
      </div>
      <p className="read-the-docs">
        Vite와 React 로고를 클릭하여 더 알아보기
      </p>
    </>
  )
}

export default App
