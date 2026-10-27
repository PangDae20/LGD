@echo off
chcp 65001 >nul
setlocal EnableExtensions
REM ==================================================================
REM  RTL Test Vector -> SPI/I2C Converter launcher (Windows)
REM   1) find Python: tool\.venv -> py -3 -> python -> python3 -> user install dirs
REM   2) require 3.9+ (skips the Microsoft Store "python" stub)
REM   3) if none: offer winget user-scope install of Python 3.12 (no admin)
REM   4) run tool\run_tool.py (packages, tkinter, iverilog check) -> GUI
REM  options: --check-only  --full  --yes  --cli
REM  if this .bat is blocked:
REM    powershell -NoProfile -ExecutionPolicy Bypass -File run_tool.ps1
REM ==================================================================
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

echo ================================================================
echo  Looking for Python 3.9+ ...
echo ================================================================
set "PYEXE="
set "PYARG="
set "TOOOLD="

call :try "%~dp0tool\.venv\Scripts\python.exe" ""
if defined PYEXE goto run
call :try "py" "-3"
if defined PYEXE goto run
call :try "python" ""
if defined PYEXE goto run
call :try "python3" ""
if defined PYEXE goto run
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do call :try "%%~fD\python.exe" ""
if defined PYEXE goto run
for /d %%D in ("%ProgramFiles%\Python3*") do call :try "%%~fD\python.exe" ""
if defined PYEXE goto run

echo.
if defined TOOOLD echo [FAIL] Python found but too old: %TOOOLD%  - need 3.9 or newer
if not defined TOOOLD echo [FAIL] No usable Python found
where winget >nul 2>&1
if errorlevel 1 goto manual
echo.
set "ANS=Y"
set /p "ANS=Install Python 3.12 now with winget? user scope, no admin needed [Y/n] "
if /i "%ANS%"=="n" goto manual
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do call :try "%%~fD\python.exe" ""
if defined PYEXE goto run
echo [FAIL] Python still not found. Close this window and run run_tool.bat again.
goto end

:manual
echo.
echo  Manual install: https://www.python.org/downloads/  - Python 3.12
echo    - check "Add python.exe to PATH" on the first screen
echo    - Customize installation: keep "tcl/tk and IDLE" checked - needed for GUI
echo  then run run_tool.bat again
start "" "https://www.python.org/downloads/"
goto end

:run
echo [ OK ] Python: %PYEXE% %PYARG%
echo.
"%PYEXE%" %PYARG% "%~dp0tool\run_tool.py" %*
if errorlevel 1 echo. & echo [FAIL] See messages above and tool\env_report.txt
goto end

REM ------------------------------------------------------------------
REM  :try <exe> <arg>   sets PYEXE/PYARG when the interpreter runs and is 3.9+
:try
if defined PYEXE goto :eof
set "C_EXE=%~1"
set "C_ARG=%~2"
echo %C_EXE%| findstr /c:"\" >nul && if not exist "%C_EXE%" goto :eof
"%C_EXE%" %C_ARG% -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,9) else 3)" >nul 2>&1
set "RC=%errorlevel%"
if "%RC%"=="0" set "PYEXE=%C_EXE%" & set "PYARG=%C_ARG%" & goto :eof
if not "%RC%"=="3" goto :eof
"%C_EXE%" %C_ARG% -c "import sys; print(sys.version.split()[0])" > "%TEMP%\rtl_pyver.txt" 2>nul
set /p TOOOLD=<"%TEMP%\rtl_pyver.txt"
set "TOOOLD=%TOOOLD% [%C_EXE%]"
goto :eof

:end
echo.
pause
endlocal
