@echo off
echo Setting up FrankChat for Windows...

REM Create a wrapper script for Windows
set SCRIPT_DIR=%~dp0
set BIN_DIR=%USERPROFILE%\bin
set WRAPPER=%BIN_DIR%\frankChat.bat

REM Create bin directory if it doesn't exist
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

echo @echo off > "%WRAPPER%"
echo python "%SCRIPT_DIR%frank" %%* >> "%WRAPPER%"

echo.
echo FrankChat installed to %WRAPPER%
echo.
echo IMPORTANT: Add %BIN_DIR% to your PATH:
echo   1. Open System Properties ^> Environment Variables
echo   2. Edit your user PATH variable
echo   3. Add: %BIN_DIR%
echo   4. Restart PowerShell
echo.
echo OR run this PowerShell command (as admin):
echo   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";%BIN_DIR%", "User")
echo.
echo Note: Make sure Python and dependencies are installed:
echo   pip install -r "%SCRIPT_DIR%requirements.txt"
echo.
pause
