@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\start-neuroteacher.ps1"
if errorlevel 1 (
  echo.
  echo COLOMBIA EXAM failed to start.
  pause
)
