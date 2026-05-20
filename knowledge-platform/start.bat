@echo off
chcp 65001 >nul
setlocal

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

echo ========================================
echo   Knowledge Platform
echo ========================================
echo.

:: Check if Python dependencies are installed (fast check)
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [1/3] Installing backend dependencies...
    pip install -r "%BACKEND%\requirements.txt" -q
) else (
    echo [1/3] Backend dependencies OK
)

:: Check if node_modules exists
if not exist "%FRONTEND%\node_modules" (
    echo [2/3] Installing frontend dependencies...
    cd /d "%FRONTEND%" && npm install
) else (
    echo [2/3] Frontend dependencies OK
)

echo [3/3] Starting services...
echo.

:: Start backend in background (no new window)
cd /d "%BACKEND%"
start "KP-Backend" /B cmd /c "uvicorn app.main:app --reload --port 8000 2>&1"

:: Start frontend in background (no new window)
cd /d "%FRONTEND%"
start "KP-Frontend" /B cmd /c "npm run dev 2>&1"

:: Wait for services to be ready
echo Waiting for services...
timeout /t 4 /nobreak >nul

echo.
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to stop all services...
pause >nul

:: Stop all
echo Stopping services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
echo Done.
