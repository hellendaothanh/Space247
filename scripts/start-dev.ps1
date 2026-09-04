# ==============================================================================
# Space247 - One-Click Development Environment Starter (PowerShell / Windows)
# Starts Docker Postgres+pgvector -> Runs Alembic Migrations -> Starts Backend & Web
# ==============================================================================

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend/web"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   Space247 Real Estate Platform - Development Starter   " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Project Root : $ProjectRoot" -ForegroundColor DarkGray
Write-Host "Backend Dir  : $BackendDir" -ForegroundColor DarkGray
Write-Host "Frontend Dir : $FrontendDir" -ForegroundColor DarkGray

# 1. Check prerequisites
Write-Host "`n[1/5] Checking environment prerequisites..." -ForegroundColor Yellow
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is required but not installed or not in PATH."
    exit 1
}
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Error "uv is required for Python management. Install: https://docs.astral.sh/uv/"
    exit 1
}
if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js / npm is required for Next.js frontend."
    exit 1
}
Write-Host "Prerequisites check passed (Docker, uv, Node.js)." -ForegroundColor Green

# 2. Start PostgreSQL container with pgvector
Write-Host "`n[2/5] Starting PostgreSQL with pgvector container..." -ForegroundColor Yellow
Push-Location $ProjectRoot
try {
    docker compose up -d postgres
} finally {
    Pop-Location
}

# 3. Wait for PostgreSQL healthcheck
Write-Host "`n[3/5] Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$maxRetries = 30
$retryCount = 0
$dbReady = $false

while ($retryCount -lt $maxRetries) {
    $status = docker inspect --format="{{.State.Health.Status}}" real_estate_postgres 2>$null
    if ($status -eq "healthy") {
        $dbReady = $true
        break
    }
    Start-Sleep -Seconds 1
    $retryCount++
    Write-Host "." -NoNewline
}

if (-not $dbReady) {
    Write-Warning "`nContainer healthcheck timed out. Attempting pg_isready..."
    $pgReady = docker exec real_estate_postgres pg_isready -U postgres -d real_estate_db 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PostgreSQL database failed to start."
        exit 1
    }
}
Write-Host "`nPostgreSQL database is ready!" -ForegroundColor Green

# 4. Run Alembic Database Migrations
Write-Host "`n[4/5] Running Alembic migrations to head..." -ForegroundColor Yellow
Push-Location $BackendDir
try {
    # Ensure .env exists
    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Copy-Item ".env.example" ".env"
        Write-Host "Created backend/.env from .env.example" -ForegroundColor DarkGray
    }
    uv run alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Alembic migrations failed."
        exit 1
    }
    Write-Host "Database schema synchronized successfully!" -ForegroundColor Green
} finally {
    Pop-Location
}

# Ensure frontend .env.local and node_modules exist
Push-Location $FrontendDir
try {
    if (-not (Test-Path ".env.local") -and (Test-Path ".env.example")) {
        Copy-Item ".env.example" ".env.local"
        Write-Host "Created frontend/web/.env.local from .env.example" -ForegroundColor DarkGray
    }
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing frontend dependencies (npm install)..." -ForegroundColor Yellow
        npm install
    }
} finally {
    Pop-Location
}

# 5. Start Backend and Frontend Services
Write-Host "`n[5/5] Launching backend (port 8080) and frontend (port 3000)..." -ForegroundColor Yellow
Write-Host "  - Backend API: http://localhost:8080" -ForegroundColor Cyan
Write-Host "  - Swagger Docs: http://localhost:8080/api/v1/docs" -ForegroundColor Cyan
Write-Host "  - Frontend Web: http://localhost:3000" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop services." -ForegroundColor DarkGray

# Launch backend in a background PowerShell job or process
$backendProcess = Start-Process -FilePath "uv" -ArgumentList "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload" -WorkingDirectory $BackendDir -PassThru

# Launch frontend in a background process
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -PassThru

try {
    Write-Host "`n[SUCCESS] Space247 services are running! Monitoring processes..." -ForegroundColor Green
    Wait-Process -Id $backendProcess.Id, $frontendProcess.Id
} finally {
    Write-Host "`nStopping Space247 development services..." -ForegroundColor Yellow
    if (-not $backendProcess.HasExited) { Stop-Process -Id $backendProcess.Id -Force }
    if (-not $frontendProcess.HasExited) { Stop-Process -Id $frontendProcess.Id -Force }
    # Clean up any orphaned child processes on Windows
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "uvicorn src.main:app|next dev" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host "Services stopped." -ForegroundColor DarkGray
}
