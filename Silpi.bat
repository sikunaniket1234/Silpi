@echo off
rem Silpi launcher - starts the background input method with no console window.
setlocal
set "DIR=%~dp0"
where pyw >nul 2>nul && (
  start "" pyw "%DIR%run_silpi.pyw"
  goto :eof
)
where pythonw >nul 2>nul && (
  start "" pythonw "%DIR%run_silpi.pyw"
  goto :eof
)
echo Silpi needs Python 3 with pythonw on PATH. >&2
exit /b 1
