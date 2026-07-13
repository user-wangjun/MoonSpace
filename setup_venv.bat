@echo off
setlocal
cd /d "%~dp0"

set "PYTHON312=%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe"

if not exist "%PYTHON312%" (
    echo [ERROR] Python 3.12 not found at:
    echo %PYTHON312%
    echo.
    echo Please install Python 3.12 or edit this script to point to your Python executable.
    exit /b 1
)

echo [1/5] Creating virtual environment .venv ...
"%PYTHON312%" -m venv .venv
if errorlevel 1 exit /b 1

echo [2/5] Upgrading pip ...
.venv\Scripts\python.exe -m ensurepip --upgrade
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo [3/5] Installing project dependencies ...
.venv\Scripts\python.exe -m pip install -r requirements.txt pytest pyinstaller
if errorlevel 1 exit /b 1

echo [4/5] Verifying installed packages ...
.venv\Scripts\python.exe -c "import pygame, pytest, PyInstaller; print('pygame/pytest/PyInstaller OK')"
if errorlevel 1 exit /b 1

echo [5/5] Running tests ...
.venv\Scripts\python.exe -m pytest
if errorlevel 1 exit /b 1

echo.
echo Setup complete.
echo Run the game with:
echo .venv\Scripts\python.exe main.py
