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
".venv\Scripts\python.exe" -m ayla_v2.diagnose
if errorlevel 1 (
    echo Nao consegui concluir o diagnostico. Confira o erro acima.
    pause
    exit /b 1
)
echo O relatorio nao inclui o conteudo das suas listas ou audio.
pause
