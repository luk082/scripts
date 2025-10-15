# MicroMelon Rover Control System Installation Script
# Creates virtual environment and installs dependencies
param([switch]$Dev, [switch]$Force, [switch]$Help)

if ($Help) {
    Write-Host "MicroMelon Rover Control System - Installation Script"
    Write-Host ""
    Write-Host "USAGE:"
    Write-Host "    .\install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "OPTIONS:"
    Write-Host "    -Dev     Install development dependencies (testing, linting, docs)"
    Write-Host "    -Force   Force reinstall of dependencies"
    Write-Host "    -Help    Show this help message"
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

# Create virtual environment
$venvPath = ".\venv"
if (-not (Test-Path $venvPath) -or $Force) {
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
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Upgrade pip in virtual environment
Write-Host "Upgrading pip in virtual environment..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies to virtual environment..." -ForegroundColor Yellow

if ($Force) {
    Write-Host "Force reinstall enabled - upgrading all packages..." -ForegroundColor Yellow
    $upgradeFlag = "--upgrade"
} else {
    $upgradeFlag = ""
}

if ($Dev) {
    Write-Host "Installing all dependencies (including development tools)..." -ForegroundColor Yellow
    pip install $upgradeFlag -r requirements.txt
} else {
    Write-Host "Installing core dependencies only..." -ForegroundColor Yellow
    pip install $upgradeFlag micromelon keyboard opencv-python mediapipe numpy scikit-learn pygame psutil
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    Write-Host "Try running as Administrator or with --user flag if you get permission errors" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
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
Write-Host "  1. Test system:      python rover.py --test-connection --target simulator"
Write-Host "  2. Configure:        python rover.py --config-wizard"
Write-Host "  3. Keyboard control: python rover.py --mode keyboard --target simulator"
Write-Host "  4. GUI control:      python rover.py --mode gui --target simulator"
Write-Host "  5. Gesture control:  python rover.py --mode gesture --target simulator"
Write-Host ""
Write-Host "HELP:" -ForegroundColor Cyan
Write-Host "  • Full command help: python rover.py --help"
Write-Host "  • System status:     python rover.py --status --target simulator"
Write-Host "  • Train gestures:    python train.py"
Write-Host ""
Write-Host "VIRTUAL ENVIRONMENT:" -ForegroundColor Cyan
Write-Host "  • Activate:     .\venv\Scripts\Activate.ps1"
Write-Host "  • Deactivate:   deactivate"
Write-Host ""
Write-Host "NOTE: Dependencies installed in virtual environment at .\venv"
Write-Host "Remember to activate the virtual environment before running commands!"
Write-Host "Happy rovering!" -ForegroundColor Green
