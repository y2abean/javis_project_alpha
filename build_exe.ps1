# PyInstaller를 이용해 GUI 앱 단일 exe로 빌드하는 스크립트
param(
    [string]$Name = "JarvisChatbot",
    [string]$Entry = "gui_chatbot.py",
    [string]$Icon = "",
    [switch]$IncludeData
)

py -3 -m pip install --upgrade pyinstaller | Out-Null

$args = @('--onefile','--name', $Name)
if ($Icon -ne '') { $args += @('--icon', $Icon) }
if ($IncludeData) {
    $cfg = Join-Path (Get-Location) 'jarvis_config.json'
    $hist = Join-Path (Get-Location) 'jarvis_history.txt'
    if (Test-Path $cfg) { $args += @('--add-data', "$cfg;.") }
    if (Test-Path $hist) { $args += @('--add-data', "$hist;.") }
}
$args += $Entry

py -3 -m PyInstaller @args

if ($LASTEXITCODE -eq 0) {
    Write-Host "빌드 성공: dist\$Name.exe"
} else {
    Write-Host "빌드 실패"
}
