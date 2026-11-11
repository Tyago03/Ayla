@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Nao encontrei a .venv. Este arquivo precisa ficar na raiz do projeto Ayla.
    echo Execute primeiro ATUALIZAR_AYLA.bat da pasta extraida.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m ayla_v2.launch
if errorlevel 1 (
    echo.
    echo Confira a mensagem acima. Se faltarem dependencias, abra INSTALAR_DEPENDENCIAS_AYLA.bat.
)
pause
