# ==================================================================
#  RTL Test Vector -> SPI/I2C Converter  실행 (Windows PowerShell, run_tool.bat 대체용)
#  실행: powershell -NoProfile -ExecutionPolicy Bypass -File .\run_tool.ps1 [--check-only|--full|--yes|--cli]
#   - 인터넷에서 받은 파일 차단 표시(Mark of the Web) 해제
#   - Python 찾기 / 버전 확인 / 없으면 winget 사용자 설치
#   - tool\run_tool.py 로 나머지 점검 후 GUI 실행
# ==================================================================
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
Set-Location -Path $PSScriptRoot

Write-Host "================================================================"
Write-Host " 다운로드 차단 표시 해제 (압축 해제한 파일 전체)"
Write-Host "================================================================"
try {
    Get-ChildItem -Path $PSScriptRoot -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue
    Write-Host "[ OK ] Unblock-File 완료"
} catch { Write-Host "[WARN] Unblock-File 실패 (무시하고 진행): $_" }

function Test-Py([string]$exe, [string[]]$pre) {
    if ($exe -match '[\\/]' -and -not (Test-Path $exe)) { return $null }
    try {
        & $exe @pre -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,9) else 3)" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return @{ exe = $exe; pre = $pre } }
        if ($LASTEXITCODE -eq 3) {
            $v = & $exe @pre -c "import sys;print(sys.version.split()[0])" 2>$null
            $script:tooOld = "$v ($exe)"
        }
    } catch { }
    return $null
}

$script:tooOld = $null
$cands = @(
    @{ exe = "tool\.venv\Scripts\python.exe"; pre = @() },
    @{ exe = "py"; pre = @("-3") },
    @{ exe = "python"; pre = @() },
    @{ exe = "python3"; pre = @() }
)
Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
    ForEach-Object { $cands += @{ exe = $_.FullName; pre = @() } }

$py = $null
foreach ($c in $cands) { $py = Test-Py $c.exe $c.pre; if ($py) { break } }

if (-not $py) {
    if ($script:tooOld) { Write-Host "[FAIL] Python 버전이 낮음: $($script:tooOld) (3.9 이상 필요)" }
    else { Write-Host "[FAIL] 실행 가능한 Python 을 찾지 못함" }
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        $ans = Read-Host "winget 으로 Python 3.12 를 사용자 영역에 설치할까요? [Y/n]"
        if ($ans -ne "n") {
            winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
            Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
                ForEach-Object { if (-not $py) { $py = Test-Py $_.FullName @() } }
        }
    }
    if (-not $py) {
        Write-Host ""
        Write-Host " 수동 설치: https://www.python.org/downloads/  (Add python.exe to PATH, tcl/tk 체크)"
        Start-Process "https://www.python.org/downloads/"
        Read-Host "Enter 를 누르면 종료"
        exit 1
    }
}

Write-Host "[ OK ] 사용할 Python: $($py.exe) $($py.pre -join ' ')"
Write-Host ""
$pre = $py.pre
& $py.exe @pre "tool\run_tool.py" @args
if ($LASTEXITCODE -ne 0) { Write-Host "`n[FAIL] 점검 또는 실행 중 문제 발생 - tool\env_report.txt 확인" }
Read-Host "Enter 를 누르면 종료"
