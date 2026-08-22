param(
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $projectRoot 'backend'
$frontend = Join-Path $projectRoot 'frontend'
$staticFrontend = Join-Path $frontend 'public'
$venvPython = Join-Path $backend '.venv\Scripts\python.exe'
$systemPython = 'C:\Python314\python.exe'
$python = if (Test-Path $systemPython) { $systemPython } else { $venvPython }
$projectRootLower = $projectRoot.ToLowerInvariant()
$logDir = Join-Path $env:TEMP 'neuroteacher-examen'
$backendOut = Join-Path $logDir 'backend.out.log'
$backendErr = Join-Path $logDir 'backend.err.log'
$frontendOut = Join-Path $logDir 'frontend.out.log'
$frontendErr = Join-Path $logDir 'frontend.err.log'

if (-not (Test-Path $python)) {
    throw "Python runtime was not found. Checked: $systemPython and $venvPython"
}
if (-not (Test-Path (Join-Path $staticFrontend 'index.html'))) {
    throw "Static frontend index was not found: $(Join-Path $staticFrontend 'index.html')"
}
if (-not (Test-Path (Join-Path $staticFrontend 'legacy-app.bundle.js'))) {
    throw "Static frontend bundle was not found: $(Join-Path $staticFrontend 'legacy-app.bundle.js')"
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
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 3
        return $health.status -eq 'ok'
    } catch {
        return $false
    }
}

function Test-Frontend {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173/' -TimeoutSec 3
        return $response.StatusCode -eq 200 `
            -and $response.Content.Contains('content="colombia-exam-static"') `
            -and $response.Content.Contains('/legacy-app.bundle.js') `
            -and $response.Content.Contains('/study-plan.js') `
            -and $response.Content.Contains('/audio-library.js')
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
    $lowerCommandLine = $commandLine.ToLowerInvariant()
    $looksLikeBackend = $ServiceName -eq 'backend' -and $lowerCommandLine.Contains('uvicorn') -and $lowerCommandLine.Contains('main:app')
    $looksLikeFrontend = $ServiceName -eq 'frontend' -and $lowerCommandLine.Contains('http.server') -and $lowerCommandLine.Contains('5173')
    $workingProcessIsOurs = $commandLine -and ($lowerCommandLine.Contains($projectRootLower) -or $looksLikeBackend -or $looksLikeFrontend)

    if ($workingProcessIsOurs) {
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

function Stop-ProjectListener([int]$Port, [string]$ServiceName) {
    $listener = Get-Listener $Port
    if (-not $listener) { return }

    $processId = [int]$listener.OwningProcess
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
    $commandLine = if ($processInfo) { [string]$processInfo.CommandLine } else { '' }
    $lowerCommandLine = $commandLine.ToLowerInvariant()
    $looksLikeBackend = $ServiceName -eq 'backend' -and $lowerCommandLine.Contains('uvicorn') -and $lowerCommandLine.Contains('main:app')
    $looksLikeFrontend = $ServiceName -eq 'frontend' -and $lowerCommandLine.Contains('http.server') -and $lowerCommandLine.Contains('5173')
    if ($commandLine -and ($lowerCommandLine.Contains($projectRootLower) -or $looksLikeBackend -or $looksLikeFrontend)) {
        Stop-OwnedListener $Port $ServiceName
    }
}

function Wait-For([scriptblock]$Probe, [int]$Seconds = 25) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        if (& $Probe) { return $true }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    return $false
}

Stop-ProjectListener 8000 'backend'
Stop-ProjectListener 5173 'frontend'

if (-not (Test-Backend)) {
    if (Test-Port 8000) { Stop-OwnedListener 8000 'backend' }
    Remove-Item $backendOut, $backendErr -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath $python `
        -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000') `
        -WorkingDirectory $backend `
        -WindowStyle Hidden `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendErr
}

if (-not (Test-Frontend)) {
    if (Test-Port 5173) { Stop-OwnedListener 5173 'frontend' }
    Remove-Item $frontendOut, $frontendErr -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath $python `
        -ArgumentList @('-m', 'http.server', '5173', '--bind', '127.0.0.1') `
        -WorkingDirectory $staticFrontend `
        -WindowStyle Hidden `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr
}

$backendReady = Wait-For { Test-Backend } 25
$frontendReady = Wait-For { Test-Frontend } 25

if (-not $backendReady -or -not $frontendReady) {
    Write-Host "Backend ready: $backendReady"
    Write-Host "Frontend ready: $frontendReady"
    if (Test-Path $backendErr) {
        Write-Host "Backend error log tail:"
        Get-Content $backendErr -Tail 20 -ErrorAction SilentlyContinue
    }
    if (Test-Path $frontendErr) {
        Write-Host "Frontend error log tail:"
        Get-Content $frontendErr -Tail 20 -ErrorAction SilentlyContinue
    }
    throw "COLOMBIA EXAM did not start correctly. Logs: $backendErr ; $frontendErr"
}

$launchId = Get-Date -Format 'yyyyMMddHHmmss'
$url = "http://127.0.0.1:5173/?static=1&launch=$launchId"
Write-Host "COLOMBIA EXAM is running: $url"
Write-Host "Logs: $logDir"
if (-not $NoBrowser) { Start-Process $url }
