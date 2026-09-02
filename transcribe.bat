@echo off
chcp 65001 >nul
REM Drag an audio or video file onto this file to get a .txt beside it.
REM This file must keep CRLF line endings; cmd.exe misparses LF-only batch files.
setlocal

if "%~1"=="" goto :usage

set "PY="
where py >nul 2>nul && set "PY=py -3"
if defined PY goto :run
where python >nul 2>nul && set "PY=python"
if defined PY goto :run
goto :nopython

:run
echo Working. The first run downloads the model, which takes a few minutes.
echo.
%PY% "%~dp0transcribe.py" %*
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Finished with errors, code %RC%.
echo Press any key to close this window.
pause >nul
exit /b %RC%

:usage
echo Drag an audio or video file onto this script.
echo.
echo Or run it from a terminal:
echo    transcribe.bat "C:\path\to\recording.mp3"
echo.
echo Press any key to close this window.
pause >nul
exit /b 1

:nopython
echo Python was not found on this machine.
echo Install it from https://www.python.org/downloads/ and tick
echo "Add python.exe to PATH" during setup, then try again.
echo.
echo Press any key to close this window.
pause >nul
exit /b 1
