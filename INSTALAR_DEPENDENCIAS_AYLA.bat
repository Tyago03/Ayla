@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 where py >nul 2>nul
 if errorlevel 1 (
  python -m venv .venv
 ) else (
  py -3 -m venv .venv
 )
)
if not exist ".venv\Scripts\python.exe" (
 echo Nao consegui criar a .venv. Instale Python 3.10 ou superior e tente novamente.
 pause
 exit /b 1
)
echo Instalando dependencias na .venv. Usa internet.
".venv\Scripts\python.exe" -m pip install -r ayla_v2\requirements-dev.txt
if errorlevel 1 echo Instalacao incompleta. Confira o erro antes de iniciar.
pause
