@echo off
title Digital Twin AI — Launcher
setlocal

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv\Scripts"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=8501"

echo ============================================
echo  Digital Twin AI — Starting...
echo ============================================
echo.

REM ── Check venv exists ──────────────────────────────────────────────────────
if not exist "%VENV%\uvicorn.exe" (
    echo [ERROR] uvicorn not found in .venv.
    echo         Run:  .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
if not exist "%VENV%\streamlit.exe" (
    echo [ERROR] streamlit not found in .venv.
    echo         Run:  .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM ── Kill any leftover processes on those ports ──────────────────────────────
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%BACKEND_PORT% "  2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%FRONTEND_PORT% " 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)

REM ── Start backend ──────────────────────────────────────────────────────────
echo [1/3] Starting backend on port %BACKEND_PORT%...
start "Digital Twin AI — Backend" /D "%ROOT%backend" "%VENV%\uvicorn.exe" ^
    main:app --host 127.0.0.1 --port %BACKEND_PORT%

REM ── Wait until backend is actually accepting connections ───────────────────
echo [2/3] Waiting for backend to be ready...
set "TRIES=0"
:wait_loop
set /a TRIES+=1
if %TRIES% GTR 30 (
    echo [ERROR] Backend did not start within 30 seconds. Check the backend window for errors.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command ^
    "try { $r=(New-Object Net.WebClient).DownloadString('http://127.0.0.1:%BACKEND_PORT%/health'); if($r -match 'ok'){exit 0} else {exit 1} } catch {exit 1}" >nul 2>&1
if errorlevel 1 goto wait_loop

echo        Backend is up ^(health check passed^).
echo.

REM ── Start frontend ─────────────────────────────────────────────────────────
echo [3/3] Starting frontend on port %FRONTEND_PORT%...
start "Digital Twin AI — Frontend" /D "%ROOT%" "%VENV%\streamlit.exe" ^
    run frontend\app.py --server.port %FRONTEND_PORT% --server.headless true

REM ── Give Streamlit a moment then open the browser ──────────────────────────
timeout /t 3 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"

echo.
echo ============================================
echo  App is running!
echo  Frontend : http://localhost:%FRONTEND_PORT%
echo  API docs : http://localhost:%BACKEND_PORT%/docs
echo.
echo  Close this window or press any key to
echo  shut down both servers.
echo ============================================
pause >nul

REM ── Shutdown ───────────────────────────────────────────────────────────────
echo Shutting down...
taskkill /fi "WindowTitle eq Digital Twin AI — Backend*"  /t /f >nul 2>&1
taskkill /fi "WindowTitle eq Digital Twin AI — Frontend*" /t /f >nul 2>&1
echo Done.
