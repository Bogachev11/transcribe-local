@echo off
REM Drag an audio or video file onto this file to get a .txt beside it.
setlocal

set PY=python
where py >nul 2>nul && set PY=py -3

if "%~1"=="" (
  echo Drag an audio or video file onto this script, or pass a path:
  echo   transcribe.bat "C:\path\to\recording.mp3"
  pause
  exit /b 1
)

%PY% "%~dp0transcribe.py" %*
echo.
pause
