param(
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $projectRoot 'backend'
$frontend = Join-Path $projectRoot 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$projectRootLower = $projectRoot.ToLowerInvariant()
$logDir = Join-Path $env:TEMP 'neuroteacher-examen'
$backendOut = Join-Path $logDir 'backend.out.log'
$backendErr = Join-Path $logDir 'backend.err.log'
$frontendOut = Join-Path $logDir 'frontend.out.log'
$frontendErr = Join-Path $logDir 'frontend.err.log'

if (-not (Test-Path $python)) {
    throw "Python environment was not found: $python"
}
if (-not (Test-Path (Join-Path $frontend 'node_modules'))) {
    throw 'Frontend dependencies were not found. Run: cd frontend; npm install'
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Get-Listener([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
}

function Test-Port([int]$Port) {
    return [bool](Get-Listener $Port)
}

function Test-Backend {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
        return $health.status -eq 'ok'
    } catch {
        return $false
    }
}

function Test-Frontend {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173/' -TimeoutSec 2
        return $response.Content.Contains('content="colombia-exam-vite"')
    } catch {
        return $false
    }
}

function Stop-OwnedListener([int]$Port, [string]$ServiceName) {
    $listener = Get-Listener $Port
    if (-not $listener) { return }

    $processId = [int]$listener.OwningProcess
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
    $commandLine = if ($processInfo) { [string]$processInfo.CommandLine } else { '' }

    if ($commandLine -and $commandLine.ToLowerInvariant().Contains($projectRootLower)) {
        Write-Host "Restarting stale $ServiceName process on port $Port (PID $processId)..."
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        for ($i = 0; $i -lt 20; $i++) {
            if (-not (Test-Port $Port)) { return }
            Start-Sleep -Milliseconds 250
        }
        throw "Could not release port $Port from the stale $ServiceName process."
    }

    throw "Port $Port is occupied by another application (PID $processId). Close that application and start COLOMBIA EXAM again."
}

function Wait-For([scriptblock]$Probe, [int]$Seconds = 20) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        if (& $Probe) { return $true }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    return $false
}

if (-not (Test-Backend)) {
    if (Test-Port 8000) {
        Stop-OwnedListener 8000 'backend'
    }
    Remove-Item $backendOut, $backendErr -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath $python `
        -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000') `
        -WorkingDirectory $backend `
        -WindowStyle Hidden `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendErr
}

if (-not (Test-Frontend)) {
    if (Test-Port 5173) {
        Stop-OwnedListener 5173 'frontend'
    }
    Remove-Item $frontendOut, $frontendErr -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath 'npm.cmd' `
        -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173', '--strictPort') `
        -WorkingDirectory $frontend `
        -WindowStyle Hidden `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr
}

$backendReady = Wait-For { Test-Backend } 20
$frontendReady = Wait-For { Test-Frontend } 20

if (-not $backendReady -or -not $frontendReady) {
    throw "COLOMBIA EXAM did not start correctly. Logs: $backendErr ; $frontendErr"
}

$launchId = Get-Date -Format 'yyyyMMddHHmmss'
$url = "http://127.0.0.1:5173/?launch=$launchId"
Write-Host "COLOMBIA EXAM is running: $url"
Write-Host "Logs: $logDir"
if (-not $NoBrowser) { Start-Process $url }
