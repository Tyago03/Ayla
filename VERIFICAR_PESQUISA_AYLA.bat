@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Nao encontrei a .venv na raiz do projeto Ayla.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m ayla_v2.check_web
set RESULT=%ERRORLEVEL%
echo.
echo O teste nao envia mensagens, listas ou audio. O relatorio nao inclui a chave.
pause
exit /b %RESULT%
