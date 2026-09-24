# ============================================================
# SentinelGuard - One-Command Startup Script
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SentinelGuard - Starting Full System" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$RootDir = $PSScriptRoot

# 1. Start Django Backend (in a dedicated window so OTP codes are visible)
Write-Host "[1/3] Starting Django Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
$BackendCmd = "cd '$RootDir\backend'; Write-Host '--- SentinelGuard Backend (Port 8000) ---' -ForegroundColor Cyan; python manage.py runserver 127.0.0.1:8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd

# 2. Start Frontend Test Page Server (in a dedicated window)
Write-Host "[2/3] Starting Test Page and Dashboard Server on http://localhost:3000 ..." -ForegroundColor Yellow
$FrontendCmd = "cd '$RootDir'; Write-Host '--- SentinelGuard Test Server (Port 3000) ---' -ForegroundColor Cyan; python -m http.server 3000 --directory test-page"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCmd

# Wait a moment for servers to spin up
Start-Sleep -Seconds 2

# 3. Open Demo Pages in Default Browser
Write-Host "[3/3] Opening Demo Login and Security Dashboard in Browser ..." -ForegroundColor Green
Start-Process "http://localhost:3000/login.html"
Start-Sleep -Milliseconds 500
Start-Process "http://localhost:3000/dashboard/"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  SentinelGuard is up and running!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  * Backend API:        http://127.0.0.1:8000/api/health/" -ForegroundColor White
Write-Host "  * Demo Login Page:    http://localhost:3000/login.html" -ForegroundColor White
Write-Host "  * Security Dashboard: http://localhost:3000/dashboard/" -ForegroundColor White
Write-Host ""
Write-Host "  Extension Setup:" -ForegroundColor Cyan
Write-Host "     If not loaded yet, go to chrome://extensions -> Load Unpacked" -ForegroundColor Gray
Write-Host "     Folder: $RootDir\extension" -ForegroundColor Gray
Write-Host ""
Write-Host "  Note on OTP Verification:" -ForegroundColor Cyan
Write-Host "     When a step-up challenge triggers, check the Backend window" -ForegroundColor Gray
Write-Host "     to copy the 6-digit development OTP code." -ForegroundColor Gray
Write-Host ""
