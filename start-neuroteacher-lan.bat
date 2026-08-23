@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\start-neuroteacher.ps1" -Lan
if errorlevel 1 (
  echo.
  echo COLOMBIA EXAM failed to start in LAN mode.
  pause
)
