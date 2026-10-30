@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==========================================
echo             Starting RideOps AI
echo ==========================================

if not exist ".venv\Scripts\python.exe" (
    echo First-time setup is required.
    call setup.bat
    if errorlevel 1 exit /b 1
)

if not exist "frontend\node_modules" (
    echo Frontend dependencies are missing. Running setup...
    call setup.bat
    if errorlevel 1 exit /b 1
)

if not exist ".env" (
    echo ERROR: .env is missing. Run setup.bat and configure the database connection.
    pause
    exit /b 1
)

echo.
echo Starting FastAPI backend at http://127.0.0.1:8000
start "RideOps AI Backend" cmd /k "cd /d ""%~dp0"" && "".venv\Scripts\python.exe"" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting React frontend at http://localhost:5173
start "RideOps AI Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 127.0.0.1"

echo.
echo RideOps AI startup commands were launched.
echo Frontend: http://localhost:5173
echo API docs: http://127.0.0.1:8000/docs
echo.
echo Keep both terminal windows open while using the application.
pause
