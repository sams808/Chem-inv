# Chem-inv Windows lab PC updater
#
# Purpose:
#   Update an existing Chem-inv installation on a Windows lab computer.
#
# What it does:
#   - checks that Git and Python are available
#   - checks that the install directory exists
#   - pulls the latest version from GitHub
#   - recreates the virtual environment if missing
#   - updates Python dependencies
#   - runs a compile check
#
# Usage from PowerShell:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\scripts\update_chem_inv_windows.ps1
#
# Or, from any location after installation:
#   powershell.exe -ExecutionPolicy Bypass -File "$env:USERPROFILE\Chem-inv\scripts\update_chem_inv_windows.ps1"

$ErrorActionPreference = "Stop"

$InstallDir = Join-Path $env:USERPROFILE "Chem-inv"
$PythonVersion = "3.11"

Write-Host "=== Chem-inv updater ===" -ForegroundColor Cyan
Write-Host "Install directory: $InstallDir"
Write-Host ""

function Test-Command {
    param([Parameter(Mandatory = $true)][string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Refresh-Path {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

Refresh-Path

if (-not (Test-Command git)) {
    Write-Host "Git was not found. Run scripts/install_chem_inv_windows.ps1 first or install Git manually." -ForegroundColor Red
    exit 1
}

if (-not (Test-Command py)) {
    Write-Host "Python launcher was not found. Run scripts/install_chem_inv_windows.ps1 first or install Python manually." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $InstallDir)) {
    Write-Host "Chem-inv install directory was not found: $InstallDir" -ForegroundColor Red
    Write-Host "Run scripts/install_chem_inv_windows.ps1 first."
    exit 1
}

Push-Location $InstallDir

try {
    git rev-parse --is-inside-work-tree | Out-Null
} catch {
    Write-Host "$InstallDir is not a Git repository." -ForegroundColor Red
    Write-Host "Move or rename this folder, then run the installer again."
    Pop-Location
    exit 1
}

Write-Host "Checking local changes..." -ForegroundColor Cyan
$Status = git status --porcelain
if ($Status) {
    Write-Host "Local uncommitted changes were detected." -ForegroundColor Yellow
    Write-Host "The updater will not overwrite local work automatically."
    Write-Host "Review these files, commit/stash them, or reinstall in a clean folder:"
    git status --short
    Pop-Location
    exit 1
}

Write-Host "Pulling latest changes from GitHub..." -ForegroundColor Cyan
git pull --ff-only

if (-not (Test-Path ".venv")) {
    Write-Host "Virtual environment missing. Recreating it..." -ForegroundColor Yellow
    py -$PythonVersion -m venv .venv
}

Write-Host "Updating Python dependencies..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

Write-Host "Running compile check..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m compileall app main.py

Pop-Location

Write-Host ""
Write-Host "=== Chem-inv update complete ===" -ForegroundColor Green
Write-Host "You can now launch Chem-inv from the desktop shortcut."
