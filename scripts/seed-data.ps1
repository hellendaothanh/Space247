# ==============================================================================
# Space247 - Database Seeding Runner Script (PowerShell / Windows)
# Provisions default accounts (admin, agent) and 28+ properties with 768-dim embeddings
# ==============================================================================

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $ProjectRoot "backend"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "         Space247 - Database Seeding Runner             " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Project Root : $ProjectRoot" -ForegroundColor DarkGray
Write-Host "Backend Dir  : $BackendDir" -ForegroundColor DarkGray

if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Error "uv is required. Install: https://docs.astral.sh/uv/"
    exit 1
}

# Ensure backend .env exists
$BackendEnv = Join-Path $BackendDir ".env"
$BackendEnvExample = Join-Path $BackendDir ".env.example"
if (-not (Test-Path $BackendEnv) -and (Test-Path $BackendEnvExample)) {
    Write-Host "Creating backend/.env from .env.example..." -ForegroundColor Yellow
    Copy-Item $BackendEnvExample $BackendEnv
}

# 1. Check if database container is running if docker is present
if (Get-Command "docker" -ErrorAction SilentlyContinue) {
    Write-Host "Verifying database container..." -ForegroundColor DarkGray
    $containerStatus = docker inspect --format="{{.State.Health.Status}}" real_estate_postgres 2>$null
    if ($containerStatus -ne "healthy") {
        Write-Host "Starting postgres container..." -ForegroundColor Yellow
        Push-Location $ProjectRoot
        docker compose up -d postgres
        Pop-Location
        Start-Sleep -Seconds 3
    }
}

# 2. Run migrations first to ensure tables exist
Push-Location $BackendDir
try {
    Write-Host "Synchronizing database schema (alembic upgrade head)..." -ForegroundColor DarkGray
    uv run alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Database migration failed. Seeding aborted."
        exit 1
    }

    # 3. Run seed script
    Write-Host "`nRunning seed script..." -ForegroundColor Cyan
    uv run python -m scripts.seed_properties
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Database seeding failed with exit code $LASTEXITCODE."
        exit 1
    }

    Write-Host "`n[SUCCESS] Space247 database seeding completed successfully!" -ForegroundColor Green
    Write-Host "Default Accounts:" -ForegroundColor White
    Write-Host "  - Admin : admin@space247.vn | Password: Password123@" -ForegroundColor White
    Write-Host "  - Agent : agent@space247.vn | Password: Password123@" -ForegroundColor White
    Write-Host "  - User  : user@space247.vn  | Password: Password123@" -ForegroundColor White
    Write-Host "  - Properties: 30 real-world listings across Hanoi and HCMC with 768-dim embeddings" -ForegroundColor White
} finally {
    Pop-Location
}
