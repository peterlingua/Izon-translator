@echo off
title Kolokuma Izon Translator - Browser App
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 web_app.py
) else (
  python web_app.py
)
if errorlevel 1 (
  echo.
  echo The browser translator could not start. Make sure Python 3.10 or newer is installed.
  pause
)
