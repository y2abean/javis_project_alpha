# Jarvis (로컬 복사)

이 저장소는 사용자의 로컬 프로젝트를 GitHub로 옮기기 위한 준비본입니다.

주요 파일
- `push_to_github.ps1` — PowerShell로 실행 가능한 푸시 도우미 스크립트입니다. 원격 URL을 인자로 받아 `.git` 초기화, `.gitignore` 생성, 커밋, 원격 추가 및 푸시를 자동으로 수행합니다.
- `.devcontainer/devcontainer.json` — (선택) GitHub Codespaces / VS Code Remote - Containers용 기본 설정입니다.

로컬에서 Git으로 푸시하는 방법
1. Git이 설치되어 있는지 확인하세요: `git --version`
2. PowerShell에서 이 저장소 루트로 이동한 뒤 스크립트를 실행합니다:

```powershell
Set-Location 'C:\Users\User\Downloads\jarvis_package'
.\push_to_github.ps1 -RemoteUrl 'https://github.com/y2abean/javis' -CommitMessage 'Initial import'
```

문제가 발생하면 터미널 출력 전체를 복사해서 공유해 주세요. 권한 문제(403)는 포크 → PR 방식으로 해결할 수 있습니다.

GitHub Codespaces 열기
1. 코드를 원격(예: `https://github.com/<your-username>/javis`)에 푸시합니다.
2. GitHub에서 리포지토리 페이지로 가서 `Code` → `Open with Codespaces` 또는 `Codespaces` 탭에서 새 Codespace를 만드세요.

추가 도움이나 `.devcontainer` 맞춤 구성이 필요하면 알려 주세요.
# 간단한 ChatGPT 스타일 챗봇

이 저장소에는 로컬에서 실행할 수 있는 간단한 ChatGPT 스타일 챗봇 예제가 있습니다.

주요 파일
- `chatbot.py`: REPL로 동작하는 챗봇. OpenAI API 키가 설정되어 있고 `openai` 패키지가 설치되어 있으면 실제 OpenAI Chat API를 사용합니다. 그렇지 않으면 간단한 규칙 기반 응답을 제공합니다.

사용법

1. (선택) OpenAI 연동을 사용하려면 `OPENAI_API_KEY` 환경변수를 설정하세요.

   # 간단한 ChatGPT 스타일 챗봇 (자비스)

   이 저장소는 터미널에서 구동되는 개인 비서 스타일의 챗봇 예제입니다.

   특징
   - 규칙 기반(fallback) 응답
   - OpenAI 연동(환경변수 또는 설정파일에 API 키를 넣으면 자동 사용)
   - 대화 기록 저장, 간단한 명령어 지원

   빠른 시작

   1) 의존성 설치

   ```powershell
   py -3 -m pip install -r .\requirements.txt
   ```

   2) OpenAI API 키 설정 (선택)

   - 현재 세션에만 설정:

   ```powershell
   $env:OPENAI_API_KEY = 'sk-여기에_실제_API_KEY'
   ```
  
   암호화된(보안) 저장

   - 암호로 보호해서 저장하려면:

   ```powershell
   py -3 .\chatbot.py --secure-set-key sk-여기에_실제_API_KEY
   # 실행 시 암호 입력을 요청합니다. 복호화하려면 --decrypt-config 옵션 사용
   ```

   복호화:

   ```powershell
   py -3 .\chatbot.py --decrypt-config
   ```

   - 설정 파일에 영구 저장(한 번만 실행):

   ```powershell
   py -3 .\chatbot.py --set-key sk-여기에_실제_API_KEY
   ```

   - 또는 제공된 스크립트 사용:

   ```powershell
   .\set_openai_env.ps1 sk-여기에_실제_API_KEY
   ```

   3) 실행 및 테스트

   ```powershell
   py -3 .\chatbot.py      # REPL 실행
   py -3 .\chatbot.py --test  # 샘플 대화 테스트
   ```

   GUI 실행

   ```powershell
   py -3 .\gui_chatbot.py
   # 또는 실행파일로 빌드 후 실행: .\dist\JarvisChatbot.exe
   ```
  
   GUI 기능 요약
   - 입력창에서 엔터로 전송
   - '복사' 버튼: 마지막 응답을 클립보드에 복사
   - '저장' 버튼: 대화 기록을 텍스트 파일로 저장


   앱(실행파일)으로 만들기(선택)
   - PyInstaller로 단일 exe를 만들 수 있습니다:

   ```powershell
   py -3 -m pip install pyinstaller
   py -3 -m PyInstaller --onefile --name JarvisChatbot chatbot.py
   ```

   생성된 실행파일은 `dist\JarvisChatbot.exe`에 위치합니다.

   테스트
   - 간단한 pytest 테스트를 추가했습니다. 다음으로 실행할 수 있습니다:

   ```powershell
   py -3 -m pytest -q
   ```

   보안
   - API 키는 절대 공개 레포지토리에 커밋하지 마세요.
   - local eval은 AST 기반으로 안전성 검사를 하지만, 아주 복잡한 입력에는 위험이 있을 수 있습니다.

   추가 개선 요청이 있으시면 GUI 포팅, 데스크톱 패키징(예: PyInstaller 추가 자동화), 또는 더 많은 명령어/플러그인 시스템을 구현해 드리겠습니다.
