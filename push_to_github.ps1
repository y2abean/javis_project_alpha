
param(
    [string]$RemoteUrl = "https://github.com/y2abean/javis.git",
    [string]$CommitMessage = "Initial import"
)

Write-Host "Push helper: 시작합니다..." -ForegroundColor Cyan

# git가 있는지 확인
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git이 시스템에 설치되어 있지 않거나 PATH에 없습니다." -ForegroundColor Yellow
    Write-Host "1) https://git-scm.com/download/win 에서 Git for Windows를 설치하세요." -ForegroundColor Yellow
    Write-Host "2) 설치 후 PowerShell을 닫았다가 다시 열고 이 스크립트를 재실행하세요." -ForegroundColor Yellow
    exit 1
}

Set-Location "$PSScriptRoot"

if (-not (Test-Path .git)) {
    git init
    git checkout -b main
    Write-Host ".git 저장소를 초기화하고 'main' 브랜치를 생성했습니다." -ForegroundColor Green
} else {
    Write-Host ".git 저장소가 이미 존재합니다." -ForegroundColor Green
}

# .gitignore 기본 생성 (없을 때)
if (-not (Test-Path .gitignore)) {
    $content = '# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
env/
venv/
build/
dist/
*.egg-info/
*.egg
.Python
.env
jarvis_history.txt
jarvis_learning_queue.jsonl
'
    $content | Out-File -Encoding UTF8 .gitignore
    Write-Host ".gitignore 파일을 생성했습니다." -ForegroundColor Green
} else {
    Write-Host ".gitignore가 이미 존재합니다." -ForegroundColor Green
}

git add -A

if ((git status --porcelain) -ne '') {
    git commit -m $CommitMessage
    Write-Host "로컬 커밋을 생성했습니다: $CommitMessage" -ForegroundColor Green
} else {
    Write-Host "커밋할 변경사항이 없습니다." -ForegroundColor Yellow
}

# 원격 설정
git remote remove origin -ErrorAction SilentlyContinue
git remote add origin $RemoteUrl
Write-Host "원격 origin을 설정했습니다: $RemoteUrl" -ForegroundColor Green

Write-Host "원격에 푸시를 시도합니다. 인증 프롬프트가 나타나면 GitHub 계정 또는 Personal Access Token(PAT)을 사용하세요." -ForegroundColor Cyan

try {
    git push -u origin main
    Write-Host "푸시가 완료되었습니다." -ForegroundColor Green
} catch {
    Write-Host "푸시 중 오류가 발생했습니다. 메시지를 확인하고 필요하면 포크 → PR 방식으로 업로드하세요." -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 2
}

Write-Host "완료: 원하시면 Codespace 설정(.devcontainer)을 추가로 구성해 드립니다." -ForegroundColor Cyan
