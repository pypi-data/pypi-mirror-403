# iFrp Installer for Windows
Write-Host "iFrp Installer" -ForegroundColor Cyan
Write-Host "==============" -ForegroundColor Cyan

# Check for package managers and install
if (Get-Command pipx -ErrorAction SilentlyContinue) {
    Write-Host "Installing with pipx..." -ForegroundColor Green
    pipx install ifrp
}
elseif (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "Installing with uv..." -ForegroundColor Green
    uv tool install ifrp
}
elseif (Get-Command pip -ErrorAction SilentlyContinue) {
    Write-Host "Installing with pip..." -ForegroundColor Green
    pip install --user ifrp
}
else {
    Write-Host "Error: No Python package manager found." -ForegroundColor Red
    Write-Host "Please install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "Run 'ifrp' to start the TUI." -ForegroundColor Cyan
