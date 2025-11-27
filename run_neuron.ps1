# 실행 스크립트: 설정 파일에 저장된 GEMINI 키가 있으면 환경변수에 적용하고 실행합니다.
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$configPath = Join-Path $scriptDir 'neuron_config.json'
if (Test-Path $configPath) {
    try {
        $json = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($json.gemini_api_key) {
            $env:GEMINI_API_KEY = $json.gemini_api_key
            Write-Host "GEMINI_API_KEY가 현재 세션에 적용되었습니다."
        }
    }
    catch {
        Write-Host "설정 파일을 읽는 중 오류가 발생했습니다: $_"
    }
}

# 실행
py -3 .\chatbot.py
