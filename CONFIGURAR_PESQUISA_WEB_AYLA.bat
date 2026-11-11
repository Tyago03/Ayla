@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Execute INSTALAR_DEPENDENCIAS_AYLA.bat primeiro.
 pause
 exit /b 1
)
echo Configurar chave de pesquisa fora do Git.
".venv\Scripts\python.exe" -m ayla_v2.setup_web
if errorlevel 1 echo A operacao nao terminou. Confira a mensagem acima.
pause
