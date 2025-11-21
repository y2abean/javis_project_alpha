param(
    [Parameter(Mandatory=$false)]
    [string]$Key
)

if (-not $Key) {
    Write-Host "Usage: .\set_openai_env.ps1 <OPENAI_API_KEY>"
    Write-Host "예: .\set_openai_env.ps1 sk-abc123..."
    exit 1
}

try {
    [Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $Key, "User")
    Write-Host "OPENAI_API_KEY가 사용자 환경변수로 설정되었습니다. 새 PowerShell 창을 열어 적용하세요."
    Write-Host "현재 세션에도 적용하려면 다음을 실행하세요:`n$env:OPENAI_API_KEY = '$Key'"
} catch {
    Write-Host "환경변수 설정 중 오류가 발생했습니다: $_"
}
