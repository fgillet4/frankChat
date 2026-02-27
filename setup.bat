@echo off
echo Setting up FrankChat for Windows...

REM Create a wrapper script for Windows
set SCRIPT_DIR=%~dp0
set WRAPPER=%USERPROFILE%\frankChat.bat

echo @echo off > "%WRAPPER%"
echo python "%SCRIPT_DIR%frank" %%* >> "%WRAPPER%"

echo.
echo FrankChat installed!
echo You can now type 'frankChat' from anywhere.
echo.
echo Note: Make sure Python and dependencies are installed:
echo   pip install -r "%SCRIPT_DIR%requirements.txt"
echo.
pause
