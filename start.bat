@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

echo ========================================
echo   Knowledge Platform
echo ========================================
echo.

:: Check and install Python dependencies
set "MISSING_DEPS="
set "FAST_CHECK=fail"

python -c "import fastapi" >nul 2>&1
if errorlevel 1 set "FAST_CHECK=fail"

if "!FAST_CHECK!" == "fail" (
    echo [1/4] Backend dependencies not found, installing...
    pip install -r "%BACKEND%\requirements.txt" -q
    if errorlevel 1 (
        echo ERROR: Failed to install backend dependencies!
        echo Please run manually: pip install -r "%BACKEND%\requirements.txt"
        pause
        exit /b 1
    )
    echo [1/4] Backend dependencies installed successfully
) else (
    echo [1/4] Checking backend dependencies...
    
    :: Detailed check of critical dependencies from requirements.txt
    set "CRITICAL_DEPS=fastapi uvicorn sqlalchemy redis apscheduler casbin pydantic httpx openai cryptography
    set "INSTALL_MISSING="
    
    for %%D in (!CRITICAL_DEPS!) do (
        python -c "import %%D" 2>nul
        if errorlevel 1 (
            set "INSTALL_MISSING=!INSTALL_MISSING! %%D"
        )
    )
    
    if defined INSTALL_MISSING (
        echo   Missing packages:!INSTALL_MISSING!
        echo   Installing missing packages...
        pip install !INSTALL_MISSING! -q
        if errorlevel 1 (
            echo   WARNING: Some packages failed to install
        ) else (
            echo   Missing packages installed
        )
    ) else (
        echo   All critical dependencies verified
    )
)

:: Check if apscheduler is available (for heatmap scheduler)
python -c "import apscheduler" 2>nul
if errorlevel 1 (
    echo [WARNING] apscheduler not installed - heatmap scheduler will be disabled
    echo   Run: pip install apscheduler
)

:: Check if casbin-async-sqlalchemy-adapter is available
python -c "import casbin_async_sqlalchemy_adapter" 2>nul
if errorlevel 1 (
    echo [WARNING] casbin async adapter not installed - RBAC may not work
    echo   Run: pip install casbin-async-sqlalchemy-adapter
)

:: Check if node_modules exists
if not exist "%FRONTEND%\node_modules" (
    echo [2/4] Installing frontend dependencies...
    cd /d "%FRONTEND%" && npm install
) else (
    echo [2/4] Frontend dependencies OK
)

:: Check if Docker containers are running
echo [3/4] Checking infrastructure services...
docker ps --format "{{.Names}}" | findstr /C:"postgres" >nul
if errorlevel 1 (
    echo   [WARNING] PostgreSQL container not running
    echo   Start with: docker compose -f "%ROOT%infra\docker-compose.yml" up -d postgres
)

docker ps --format "{{.Names}}" | findstr /C:"redis" >nul
if errorlevel 1 (
    echo   [WARNING] Redis container not running
    echo   Start with: docker compose -f "%ROOT%infra\docker-compose.yml" up -d redis
)

echo [4/4] Starting services...
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
