# MicroMelon Rover Control System Installation Script
param([switch]$Dev, [switch]$Force, [switch]$Help)

if ($Help) {
    Write-Host "MicroMelon Rover Control System - Installation Script"
    Write-Host ""
    Write-Host "USAGE:"
    Write-Host "    .\install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "OPTIONS:"
    Write-Host "    -Dev     Install development dependencies"
    Write-Host "    -Force   Force reinstall"
    Write-Host "    -Help    Show this help"
    exit 0
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "MicroMelon Rover Control System - Installation" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}
Write-Host "Found Python: $pythonVersion" -ForegroundColor Green

# Virtual environment
$venvPath = "rover_env"
if ((Test-Path $venvPath) -and (-not $Force)) {
    Write-Host "Using existing virtual environment" -ForegroundColor Green
    & "$venvPath\Scripts\Activate.ps1"
} else {
    if (Test-Path $venvPath) {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
    }
    
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "$venvPath\Scripts\Activate.ps1"
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
if ($Dev) {
    pip install -r requirements.txt
} else {
    pip install micromelon keyboard opencv-python mediapipe numpy scikit-learn pygame psutil
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create config
if (-not (Test-Path "rover_config.json")) {
    Write-Host "Creating default configuration..." -ForegroundColor Yellow
    python -c "from config import create_default_config_file; create_default_config_file()"
}

# Final message
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "GETTING STARTED:" -ForegroundColor Cyan
Write-Host "  1. Test system:     python rover.py --test-connection --target simulator"
Write-Host "  2. Configuration:   python rover.py --config-wizard"
Write-Host "  3. Start simulator: python rover.py --mode keyboard --target simulator"
Write-Host ""
Write-Host "For help: python rover.py --help"
Write-Host ""
Write-Host "Happy rovering!" -ForegroundColor Green