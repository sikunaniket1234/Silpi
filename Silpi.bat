@echo off
:: ============================================================
::  Silpi (ଶିଳ୍ପୀ) – Universal Odia Typing Suite
::  Self-contained bootstrap launcher
::  Crafted with love by Aniket Nayak
:: ============================================================
setlocal EnableDelayedExpansion
set "DIR=%~dp0"
set "MIN_PY_MAJOR=3"
set "MIN_PY_MINOR=8"

echo.
echo  ██████╗ ██╗██╗     ██████╗ ██╗
echo  ██╔════╝ ██║██║     ██╔══██╗██║
echo  ╚█████╗  ██║██║     ██████╔╝██║
echo   ╚═══██╗ ██║██║     ██╔═══╝ ██║
echo  ██████╔╝ ██║███████╗██║     ██║
echo  ╚═════╝  ╚═╝╚══════╝╚═╝     ╚═╝
echo             ଶିଳ୍ପୀ  —  Universal Odia Typing Suite
echo             Crafted by Aniket Nayak
echo.

:: -----------------------------------------------------------
:: STEP 1: Locate a usable Python interpreter
:: -----------------------------------------------------------
set "PYEXE="
set "PYWEXE="

:: Try the Python Launcher (py.exe) first — most reliable on Windows
where py >nul 2>nul
if %errorlevel%==0 (
    for /f "tokens=*" %%V in ('py -3 --version 2^>^&1') do set "PY_VER_LINE=%%V"
    call :check_version "!PY_VER_LINE!"
    if !VER_OK!==1 (
        set "PYEXE=py -3"
        set "PYWEXE=pyw -3"
        goto :have_python
    )
)

:: Try python3 / python
for %%C in (python3 python) do (
    where %%C >nul 2>nul
    if !errorlevel!==0 (
        for /f "tokens=*" %%V in ('%%C --version 2^>^&1') do set "PY_VER_LINE=%%V"
        call :check_version "!PY_VER_LINE!"
        if !VER_OK!==1 (
            set "PYEXE=%%C"
            set "PYWEXE=%%Cw"
            goto :have_python
        )
    )
)

:: -----------------------------------------------------------
:: STEP 2: Python not found — attempt to install it
:: -----------------------------------------------------------
echo [Silpi] Python 3.8 or newer was not found on this computer.
echo [Silpi] Attempting to install Python automatically...
echo.

:: Try winget (available on Windows 10 1709+ / Windows 11)
where winget >nul 2>nul
if %errorlevel%==0 (
    echo [Silpi] Installing Python via winget (this may take a minute)...
    winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    if !errorlevel!==0 (
        echo [Silpi] Python installed successfully via winget!
        :: Refresh PATH
        call :refresh_path
        where py >nul 2>nul
        if !errorlevel!==0 (
            set "PYEXE=py -3"
            set "PYWEXE=pyw -3"
            goto :have_python
        )
    )
)

:: Winget failed / not available — open Microsoft Store or download page
echo [Silpi] Automatic installation was not possible.
echo [Silpi] Opening the Python download page in your browser...
echo.
echo  Please install Python 3.8 or newer from:
echo    https://www.python.org/downloads/
echo.
echo  IMPORTANT: Check "Add Python to PATH" during installation, then
echo  double-click Silpi.bat again to launch Silpi.
echo.
start "" "https://www.python.org/downloads/"
pause
exit /b 1

:: -----------------------------------------------------------
:: STEP 3: Python found — launch Silpi
:: -----------------------------------------------------------
:have_python
echo [Silpi] Python found: !PY_VER_LINE!
echo [Silpi] Starting Silpi...

:: Use pythonw / pyw to run without a terminal window
where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw -3 "%DIR%run_silpi.pyw"
    goto :done
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%DIR%run_silpi.pyw"
    goto :done
)
:: Fallback: use python with pythonw equivalent flag
start "" !PYEXE! "%DIR%run_silpi.pyw"

:done
echo [Silpi] Silpi has been launched. Look for the tray icon (bottom-right near the clock).
echo [Silpi] Press Ctrl+Alt+O to toggle Odia typing on/off.
timeout /t 3 /nobreak >nul
exit /b 0

:: -----------------------------------------------------------
:: Subroutine: parse "Python X.Y.Z" and set VER_OK=1 if >= 3.8
:: -----------------------------------------------------------
:check_version
set "VER_OK=0"
set "_vline=%~1"
:: Extract major.minor from "Python X.Y.Z"
for /f "tokens=2 delims= " %%A in ("!_vline!") do set "_ver=%%A"
for /f "tokens=1,2 delims=." %%M in ("!_ver!") do (
    set "_maj=%%M"
    set "_min=%%N"
)
if not defined _maj goto :eof
if not defined _min goto :eof
if !_maj! GTR %MIN_PY_MAJOR% set "VER_OK=1" & goto :eof
if !_maj! EQU %MIN_PY_MAJOR% (
    if !_min! GEQ %MIN_PY_MINOR% set "VER_OK=1"
)
goto :eof

:: -----------------------------------------------------------
:: Subroutine: attempt to refresh PATH after winget install
:: -----------------------------------------------------------
:refresh_path
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USERPATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSPATH=%%B"
set "PATH=!SYSPATH!;!USERPATH!;%PATH%"
goto :eof
