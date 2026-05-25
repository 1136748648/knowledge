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

:: Check and install Python dependencies (with error tolerance)
echo [1/5] Checking backend dependencies...

python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo   FastAPI not found, installing dependencies...
    pip install -r "%BACKEND%\requirements.txt"
    if errorlevel 1 (
        echo.
        echo   [WARNING] Some dependencies installation had issues - proceeding anyway
        echo   You may need to install Visual C++ Build Tools for some packages
        echo   Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
        echo.
    )
) else (
    echo   FastAPI found
)

:: Check critical packages one by one and install missing ones
echo   Checking individual packages...
set "CRITICAL_DEPS=fastapi uvicorn sqlalchemy redis apscheduler casbin pydantic httpx openai cryptography casbin_async_sqlalchemy_adapter"

for %%D in (!CRITICAL_DEPS!) do (
    python -c "import %%D" 2>nul
    if errorlevel 1 (
        echo   Missing: %%D
        echo   Installing: %%D...
        pip install %%D -q
        if errorlevel 1 (
            echo   [WARNING] %%D failed to install
        )
    )
)
echo   Done.

:: Check if apscheduler is available
python -c "import apscheduler" 2>nul
if errorlevel 1 (
    echo.
    echo [WARNING] apscheduler not installed - heatmap scheduler will be disabled
    echo   Run: pip install apscheduler
)

:: Check if casbin-async-sqlalchemy-adapter is available
python -c "import casbin_async_sqlalchemy_adapter" 2>nul
if errorlevel 1 (
    echo.
    echo [WARNING] casbin async adapter not installed - RBAC may not work
    echo   Run: pip install casbin-async-sqlalchemy-adapter
)

:: Check if node_modules exists and verify key dependencies
if not exist "%FRONTEND%\node_modules" (
    echo [2/5] Installing frontend dependencies...
    cd /d "%FRONTEND%" && npm install
) else (
    echo [2/5] Checking frontend dependencies...
    set "FRONTEND_OK=1"
    
    :: Check critical frontend packages
    set "FRONTEND_DEPS=crypto-js axios element-plus vue vue-router vue-i18n pinia"
    
    for %%D in (!FRONTEND_DEPS!) do (
        if not exist "%FRONTEND%\node_modules\%%D" (
            echo   Missing: %%D
            set "FRONTEND_OK=0"
        )
    )
    
    if "!FRONTEND_OK!" == "0" (
        echo   Reinstalling dependencies...
        cd /d "%FRONTEND%" && npm install
    ) else (
        echo   Frontend dependencies OK
    )
)

:: Check if Docker containers are running
echo [3/5] Checking infrastructure services...
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

echo [4/5] Starting backend...
echo.

:: Start backend and wait for it to be ready
cd /d "%BACKEND%"
start "KP-Backend" /B cmd /c "uvicorn app.main:app --reload --port 8000 2>&1"

:: Wait for backend to be ready (check health endpoint)
echo   Waiting for backend to start...
set "BACKEND_READY=0"
for /L %%i in (1,1,30) do (
    curl -s http://localhost:8000/docs >nul 2>&1
    if not errorlevel 1 (
        set "BACKEND_READY=1"
        echo   Backend is ready!
        goto :backend_ready
    )
    timeout /t 1 /nobreak >nul
)

:backend_ready
if "!BACKEND_READY!" == "0" (
    echo   [WARNING] Backend may not be ready, continuing anyway...
)

echo [5/5] Starting frontend...

:: Start frontend in background (no new window)
cd /d "%FRONTEND%"
start "KP-Frontend" /B cmd /c "npm run dev 2>&1"

:: Wait for frontend to be ready
echo   Waiting for frontend to start...
timeout /t 3 /nobreak >nul

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
