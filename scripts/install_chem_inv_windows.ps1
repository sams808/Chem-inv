# Chem-inv Windows lab PC installer
#
# Purpose:
#   Set up Chem-inv on a Windows lab computer with minimal manual work.
#
# What it does:
#   - checks for winget
#   - installs Git if needed
#   - installs Python 3.11 if needed
#   - clones or updates the Chem-inv repository
#   - creates a local virtual environment
#   - installs Python dependencies
#   - runs a compile check
#   - creates a launch script
#   - creates a desktop shortcut
#
# Usage from PowerShell:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\scripts\install_chem_inv_windows.ps1
#
# Notes:
#   Run this as the Windows user who will use the app.
#   This script requires internet access for Git, Python, and Python packages.

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/sams808/Chem-inv.git"
$InstallDir = Join-Path $env:USERPROFILE "Chem-inv"
$PythonVersion = "3.11"
$PythonWingetId = "Python.Python.3.11"
$GitWingetId = "Git.Git"

Write-Host "=== Chem-inv Windows installer ===" -ForegroundColor Cyan
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

if (-not (Test-Command winget)) {
    Write-Host "winget was not found on this computer." -ForegroundColor Red
    Write-Host "Install 'App Installer' from the Microsoft Store, or install Git and Python manually."
    exit 1
}

if (-not (Test-Command git)) {
    Write-Host "Git not found. Installing Git..." -ForegroundColor Yellow
    winget install --id $GitWingetId -e --source winget
    Refresh-Path
} else {
    Write-Host "Git found." -ForegroundColor Green
}

if (-not (Test-Command py)) {
    Write-Host "Python launcher not found. Installing Python $PythonVersion..." -ForegroundColor Yellow
    winget install --id $PythonWingetId -e --source winget
    Refresh-Path
} else {
    Write-Host "Python launcher found." -ForegroundColor Green
}

Write-Host "Checking Python $PythonVersion..." -ForegroundColor Cyan
try {
    py -$PythonVersion --version
} catch {
    Write-Host "Python $PythonVersion is not available through the Python launcher." -ForegroundColor Red
    Write-Host "Try closing and reopening PowerShell, then rerun this script."
    exit 1
}

if (-not (Test-Path $InstallDir)) {
    Write-Host "Cloning Chem-inv..." -ForegroundColor Cyan
    git clone $RepoUrl $InstallDir
} else {
    Write-Host "Chem-inv directory already exists. Updating repository..." -ForegroundColor Cyan
    Push-Location $InstallDir
    git pull
    Pop-Location
}

Push-Location $InstallDir

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    py -$PythonVersion -m venv .venv
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

Write-Host "Running compile check..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m compileall app main.py

$LauncherPath = Join-Path $InstallDir "launch_chem_inv.ps1"
$LauncherContent = @"
Set-Location "$InstallDir"
& ".\.venv\Scripts\python.exe" "main.py"
"@
Set-Content -Path $LauncherPath -Value $LauncherContent -Encoding UTF8

$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Chem-inv.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$LauncherPath`""
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.WindowStyle = 1
$Shortcut.Description = "Launch Chem-inv chemical inventory app"
$Shortcut.Save()

Pop-Location

Write-Host ""
Write-Host "=== Chem-inv installation complete ===" -ForegroundColor Green
Write-Host "Install folder: $InstallDir"
Write-Host "Desktop shortcut: $ShortcutPath"
Write-Host ""
Write-Host "Launch Chem-inv from the desktop shortcut or run:"
Write-Host "  powershell.exe -ExecutionPolicy Bypass -File `"$LauncherPath`""
