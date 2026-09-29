@echo off
cd /d "%~dp0"
python server.py
if errorlevel 1 (
  echo.
  echo The web application could not start. Install Python and run:
  echo python -m pip install -r requirements.txt
  pause
)
