@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Nao encontrei a .venv. Este arquivo precisa ficar na raiz do projeto Ayla.
    pause
    exit /b 1
)
echo Avaliacao do CLASSIFICADOR LEGADO de tarefas, nao do chat geral.
echo Para o agente novo, use AVALIAR_AGENTE_AYLA.bat.
echo Nao altera listas, nao consulta o clima e nao executa os casos reservados.
echo Mantenha o Ollama aberto e evite enviar mensagens durante a avaliacao.
echo.
".venv\Scripts\python.exe" -m ayla_v2.evaluate --split dev
if errorlevel 1 (
    echo.
    echo A avaliacao nao terminou. Confira a mensagem acima.
    pause
    exit /b 1
)
if exist "ayla_v2\evaluation\results" start "" "ayla_v2\evaluation\results"
pause
