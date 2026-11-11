@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Nao encontrei a .venv. Este arquivo precisa ficar na raiz do projeto Ayla.
    echo Execute primeiro INSTALAR_DEPENDENCIAS_AYLA.bat na raiz do projeto.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pytest ayla_v2\tests -q -ra
set "TEST_RESULT=%ERRORLEVEL%"
echo.
if "%TEST_RESULT%"=="0" (
    echo Verificacao concluida sem falhas nos testes executados.
    echo Se houver SKIPPED, leia o motivo acima: nao significa teste aprovado.
) else (
    echo A verificacao terminou com erro. Confira o resumo acima.
)
echo.
echo Estes testes usam respostas simuladas. A avaliacao do Qwen real e uma etapa separada.
pause
exit /b %TEST_RESULT%
