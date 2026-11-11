@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Nao encontrei a .venv. Abra este arquivo na raiz do projeto Ayla.
    pause
    exit /b 1
)
echo DITADO LOCAL OPCIONAL - Whisper base
echo Este preparo instala bibliotecas e baixa um modelo publico usando internet.
echo Depois, o audio sera processado neste computador, no processador.
echo O chat e a leitura em voz alta funcionam sem este complemento.
echo Encerre o servidor da Ayla antes da instalacao. Nao precisa fechar o Ollama.
echo.
choice /C SN /N /M "Instalar o ditado local? [S/N]: "
if errorlevel 2 exit /b 0
".venv\Scripts\python.exe" -m pip install -r ayla_v2\requirements-voice.txt
if errorlevel 1 (
    echo A instalacao das bibliotecas falhou. O chat nao foi alterado.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m ayla_v2.speech
if errorlevel 1 (
    echo O modelo nao ficou pronto. Confira a conexao e o erro acima.
    echo Voce pode continuar usando texto ou ditado do navegador com consentimento.
    pause
    exit /b 1
)
echo Pronto. Abra INICIAR_AYLA.bat. Em Voz e microfone, use Automatico ou Somente local.
pause
