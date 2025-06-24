@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set MCP_DEBUG=1

set VENV_DIR=%~dp0.venv310
set PYTHON_EXEC=%VENV_DIR%\Scripts\python.exe

if not exist "%PYTHON_EXEC%" (
    echo Error: Python virtual environment not found at %VENV_DIR%
    pause
    exit /b 1
)

echo Starting MCP ChromaDB Server...
echo Python: %PYTHON_EXEC%
echo Working Directory: %~dp0

"%PYTHON_EXEC%" -c "import sys; print('Python Path:', sys.path)"

"%PYTHON_EXEC%" -m src.fastmcp_main_modular

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Server exited with error code %ERRORLEVEL%
    pause
)

exit /b %ERRORLEVEL%
