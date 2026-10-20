@echo off
setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"
set "PS1=%SCRIPT_DIR%init-video-workflow.ps1"

if not exist "%PS1%" (
    echo ERROR: init-video-workflow.ps1 not found next to this batch file.
    pause
    exit /b 40
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %*
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    if not "%EXITCODE%"=="2" (
        echo.
        echo Installation failed with exit code %EXITCODE%.
    )
)

exit /b %EXITCODE%
