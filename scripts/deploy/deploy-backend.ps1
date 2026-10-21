
param(
    [Parameter(Mandatory = $true)]
    [string]$StagingDir,

    [Parameter(Mandatory = $true)]
    [string]$BackendDir,

    [int]$Port = 443,

    [string]$SslCertFile = "certificate.crt",

    [string]$SslKeyFile = "private.key",

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

trap {
    Write-Host ""
    Write-Host "========== DEPLOY ERROR =========="
    Write-Host "Message: $($_.Exception.Message)"
    Write-Host "Line: $($_.InvocationInfo.ScriptLineNumber)"
    Write-Host "Command: $($_.InvocationInfo.Line)"
    Write-Host "Stack: $($_.ScriptStackTrace)"
    Write-Host "=================================="
    exit 1
}

# --------------------------------------------------
# Functions
# --------------------------------------------------

function Stop-ProcessTree {
    param(
        [int]$ProcessId
    )

    if ($ProcessId -le 0) {
        return
    }

    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue

    if ($null -ne $process) {
        Write-Host "Stopping process tree: $ProcessId"

        & taskkill.exe /PID $ProcessId /T /F | Out-Host

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to stop process $ProcessId"
        }
    }
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [string[]]$Arguments = @()
    )

    if ([string]::IsNullOrWhiteSpace($FilePath)) {
        throw "Executable path is null or empty."
    }

    Write-Host "Executing: $FilePath $($Arguments -join ' ')"

    & $FilePath @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

function Test-PortListening {
    param([int]$ListenPort)

    $connection = Get-NetTCPConnection `
        -LocalPort $ListenPort `
        -State Listen `
        -ErrorAction SilentlyContinue

    return $null -ne $connection
}

# --------------------------------------------------
# 0. Validate configuration
# --------------------------------------------------

Write-Host "========== DEPLOY START =========="
Write-Host "StagingDir: $StagingDir"
Write-Host "BackendDir: $BackendDir"
Write-Host "Port: $Port"

if ([string]::IsNullOrWhiteSpace($StagingDir)) {
    throw "StagingDir is empty."
}

if ([string]::IsNullOrWhiteSpace($BackendDir)) {
    throw "BackendDir is empty."
}

$stagedApp = Join-Path $StagingDir "app"
$stagedRequirements = Join-Path $StagingDir "requirements.txt"

if (-not (Test-Path -LiteralPath $stagedApp -PathType Container)) {
    throw "Staged app directory not found: $stagedApp"
}

if (-not (Test-Path -LiteralPath $stagedRequirements -PathType Leaf)) {
    throw "requirements.txt not found: $stagedRequirements"
}

New-Item -ItemType Directory -Force -Path $BackendDir | Out-Null

$appDir = Join-Path $BackendDir "app"
$pidFile = Join-Path $BackendDir "backend.pid"
$logFile = Join-Path $BackendDir "backend.log"

$certPath = Join-Path $BackendDir $SslCertFile
$keyPath = Join-Path $BackendDir $SslKeyFile

$venvDir = Join-Path $BackendDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

# SSL certificate validation
if (-not (Test-Path -LiteralPath $certPath -PathType Leaf)) {
    throw "SSL certificate not found: $certPath"
}

if (-not (Test-Path -LiteralPath $keyPath -PathType Leaf)) {
    throw "SSL private key not found: $keyPath"
}

Write-Host "SSL certificate: $certPath"
Write-Host "SSL private key: $keyPath"

# --------------------------------------------------
# 1. Prepare Python environment
# --------------------------------------------------

Write-Host ""
Write-Host "========== PYTHON ENV =========="

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {

    Write-Host "Creating virtual environment..."

    Invoke-Native -FilePath $Python -Arguments @(
        "-m",
        "venv",
        $venvDir
    )
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    throw "Virtual environment Python not found: $venvPython"
}

Write-Host "Installing dependencies..."

Invoke-Native -FilePath $venvPython -Arguments @(
    "-m",
    "pip",
    "install",
    "--disable-pip-version-check",
    "-q",
    "-r",
    $stagedRequirements
)

Write-Host "Dependencies installed."

# --------------------------------------------------
# 2. Stop existing backend
# --------------------------------------------------

Write-Host ""
Write-Host "========== STOP BACKEND =========="

# Stop process recorded in PID file.
if (Test-Path -LiteralPath $pidFile) {

    $oldPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()

    if ($oldPid -match '^\d+$') {
        Stop-ProcessTree -ProcessId ([int]$oldPid)
    }

    Remove-Item -LiteralPath $pidFile -Force
}

# Stop processes listening on the backend port.
$listeners = @(
    Get-NetTCPConnection `
        -LocalPort $Port `
        -State Listen `
        -ErrorAction SilentlyContinue
)

$ownerPids = @(
    $listeners |
        Where-Object { $null -ne $_ } |
        Select-Object -ExpandProperty OwningProcess -Unique
)

foreach ($ownerPid in $ownerPids) {
    Stop-ProcessTree -ProcessId ([int]$ownerPid)
}

# Wait for the port to become available.
for ($i = 0; $i -lt 20; $i++) {

    if (-not (Test-PortListening -ListenPort $Port)) {
        break
    }

    Start-Sleep -Seconds 1
}

if (Test-PortListening -ListenPort $Port) {
    throw "Port $Port is still in use."
}

Write-Host "Backend stopped."

# --------------------------------------------------
# 3. Deploy application
# --------------------------------------------------

Write-Host ""
Write-Host "========== DEPLOY FILES =========="

# Replace application directory.
if (Test-Path -LiteralPath $appDir) {

    Write-Host "Removing old app directory..."

    Remove-Item `
        -LiteralPath $appDir `
        -Recurse `
        -Force
}

Write-Host "Copying new app files..."

Copy-Item `
    -LiteralPath $stagedApp `
    -Destination $appDir `
    -Recurse `
    -Force

Copy-Item `
    -LiteralPath $stagedRequirements `
    -Destination (Join-Path $BackendDir "requirements.txt") `
    -Force

Write-Host "Application files deployed."

# Preserve:
# .env
# app.db
# .venv
# certificate.crt
# private.key
# backend.log

# --------------------------------------------------
# 4. Start Uvicorn HTTPS server
# --------------------------------------------------

Write-Host ""
Write-Host "========== START BACKEND =========="

$envFile = Join-Path $BackendDir ".env"

if (-not (Test-Path -LiteralPath $envFile)) {
    Write-Warning ".env file not found: $envFile"
}

# Use absolute SSL paths.
$uvicornArgs = @(
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "$Port",
    "--ssl-certfile",
    $certPath,
    "--ssl-keyfile",
    $keyPath
)

# Build the command line.
$quotedPython = '"' + $venvPython + '"'

$argumentLine = (
    $uvicornArgs | ForEach-Object {
        if ($_ -match '\s') {
            '"' + $_ + '"'
        }
        else {
            $_
        }
    }
) -join " "

$quotedLog = '"' + $logFile + '"'

$commandLine = 'cmd.exe /d /s /c ""' +
    $venvPython +
    '" ' +
    $argumentLine +
    ' >> ' +
    $quotedLog +
    ' 2>&1"'

Write-Host "Starting Uvicorn..."
Write-Host "Working directory: $BackendDir"

# Create a process independent of the SSH session.
$result = Invoke-CimMethod `
    -ClassName Win32_Process `
    -MethodName Create `
    -Arguments @{
        CommandLine      = $commandLine
        CurrentDirectory = $BackendDir
    }

if ($result.ReturnValue -ne 0) {
    throw "Failed to start backend. CIM return code: $($result.ReturnValue)"
}

$newPid = $result.ProcessId

Set-Content `
    -LiteralPath $pidFile `
    -Value $newPid `
    -Encoding ascii

Write-Host "Backend process created."
Write-Host "PID: $newPid"
Write-Host "Port: $Port"

# --------------------------------------------------
# 5. Verify startup
# --------------------------------------------------

Write-Host ""
Write-Host "========== VERIFY BACKEND =========="

$started = $false

for ($i = 0; $i -lt 30; $i++) {

    if (Test-PortListening -ListenPort $Port) {
        $started = $true
        break
    }

    Start-Sleep -Seconds 1
}

if (-not $started) {

    Write-Host "Backend failed to listen on port $Port"

    if (Test-Path -LiteralPath $logFile) {
        Write-Host "========== BACKEND LOG =========="
        Get-Content -LiteralPath $logFile -Tail 50 | Out-Host
    }

    throw "Backend startup verification failed."
}

Write-Host "Backend is listening on port $Port"

# Clean staging files only after startup succeeds.
if (Test-Path -LiteralPath $StagingDir) {
    Remove-Item -LiteralPath $StagingDir -Recurse -Force
}

Write-Host ""
Write-Host "========== DEPLOY SUCCESS =========="
Write-Host "BackendDir: $BackendDir"
Write-Host "URL: https://localhost:$Port"
Write-Host "===================================="

exit 0
