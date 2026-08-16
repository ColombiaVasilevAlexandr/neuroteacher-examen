param(
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $projectRoot 'backend'
$frontend = Join-Path $projectRoot 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw "Python environment was not found: $python"
}
if (-not (Test-Path (Join-Path $frontend 'node_modules'))) {
    throw 'Frontend dependencies were not found. Run: cd frontend; npm install'
}

function Test-Port([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

if (-not (Test-Port 8000)) {
    Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $backend -WindowStyle Hidden
}

if (-not (Test-Port 5173)) {
    Start-Process -FilePath 'npm.cmd' -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173') -WorkingDirectory $frontend -WindowStyle Hidden
}

Start-Sleep -Seconds 2
if (-not (Test-Port 8000) -or -not (Test-Port 5173)) {
    throw 'The application did not start. Check the backend and frontend.'
}

$url = 'http://127.0.0.1:5173/'
Write-Host "Application is running: $url"
if (-not $NoBrowser) { Start-Process $url }
