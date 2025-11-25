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
