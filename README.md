# NEURON (뉴런)

**NEURON**은 Google Gemini 2.0 Flash 모델을 기반으로 한 지능형 AI 챗봇 프로젝트입니다. Python Flask 백엔드와 React(Vite) 프론트엔드로 구성되어 있으며, 사용자 친화적인 웹 인터페이스를 제공합니다.

## ✨ 주요 기능

- **강력한 AI 대화**: Google Gemini 2.0 Flash 모델을 사용하여 빠르고 정확한 답변 제공
- **Markdown 지원**: 답변 내용을 보기 좋게 렌더링 (문단, 리스트, 코드 블록, 볼드체 등)
- **반응형 UI**: 메시지 길이에 따라 자동으로 조절되는 말풍선 및 깔끔한 디자인
- **지식 저장**: 대화 내용을 학습하고 기억하는 기능 (개발 중)
- **명령어 시스템**: `/help`, `/clear` 등 다양한 명령어 지원

## 🚀 설치 및 실행 방법

### 1. 필수 요구 사항
- Python 3.8 이상
- Node.js 및 npm
- Google Gemini API 키

### 2. 설치

```bash
# 패키지 설치
pip install -r requirements.txt

# 프론트엔드 의존성 설치
cd vite-react-app
npm install
```

### 3. API 키 설정

`.env` 파일을 생성하거나 `neuron_config.json`을 통해 API 키를 설정합니다.

**.env 파일 예시:**
```env
GEMINI_API_KEY=AIzaSy...
```

### 4. 실행

**백엔드 (서버)**
```bash
# 프로젝트 루트에서
py server.py
```

**프론트엔드 (웹 앱)**
```bash
# vite-react-app 폴더에서
npm run dev
```

브라우저에서 `http://localhost:5173`으로 접속하여 사용합니다.

## 📁 프로젝트 구조

- `chatbot.py`: 챗봇 핵심 로직 및 Gemini API 연동
- `server.py`: Flask 백엔드 서버
- `vite-react-app/`: React 프론트엔드 소스
  - `src/components/ChatWindow.jsx`: 채팅 UI 컴포넌트 (Markdown 적용)
- `neuron_config.json`: 사용자 설정 파일
- `neuron_history.txt`: 대화 기록 저장

## 📝 라이선스

이 프로젝트는 개인 학습 및 연구 목적으로 제작되었습니다.
