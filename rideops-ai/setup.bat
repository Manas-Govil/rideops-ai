@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==========================================
echo       RideOps AI - First-time setup
echo ==========================================
echo.

where py >nul 2>nul
if not errorlevel 1 (
    py -3.13 --version >nul 2>nul && set "PYTHON_CMD=py -3.13"
    if not defined PYTHON_CMD py -3 --version >nul 2>nul && set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo ERROR: Python 3.11-3.13 was not found.
    echo Install Python from https://www.python.org/downloads/
    echo During installation, enable "Add Python to PATH".
    pause
    exit /b 1
)

echo Using Python:
%PYTHON_CMD% --version
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :error
)

echo.
echo Installing backend dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

if not exist ".env" (
    echo.
    echo Creating .env from .env.example...
    copy ".env.example" ".env" >nul
    echo IMPORTANT: Edit .env and set your PostgreSQL password before running the app.
)

if not exist "frontend\package.json" (
    echo ERROR: frontend\package.json was not found.
    goto :error
)

where npm >nul 2>nul
if errorlevel 1 (
    echo ERROR: npm was not found. Install Node.js LTS from https://nodejs.org/
    goto :error
)

echo.
echo Installing frontend dependencies...
pushd frontend
call npm ci
if errorlevel 1 (
    popd
    goto :error
)
popd

echo.
echo Setup completed.
echo Next: configure .env, create the PostgreSQL database, load the schema and data.
echo Then run start.bat.
pause
exit /b 0

:error
echo.
echo Setup failed. Read the error above, fix the prerequisite, and run setup.bat again.
pause
exit /b 1
