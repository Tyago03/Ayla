@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Coloque ESTE arquivo e detalhar_pesquisa_ayla.py na raiz do projeto Ayla.
    echo E a mesma pasta que contem a .venv e INICIAR_AYLA.bat.
    echo Nao e necessario instalar ou trocar nenhuma versao da Ayla.
    pause
    exit /b 2
)
if not exist "detalhar_pesquisa_ayla.py" (
    echo Extraia tambem detalhar_pesquisa_ayla.py ao lado deste atalho.
    pause
    exit /b 2
)
".venv\Scripts\python.exe" -X utf8 "detalhar_pesquisa_ayla.py"
set RESULT=%ERRORLEVEL%
echo.
echo Este teste nao modifica a configuracao. Nunca compartilhe web-secret.json.
pause
exit /b %RESULT%
