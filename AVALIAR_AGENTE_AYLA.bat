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
".venv\Scripts\python.exe" -m ayla_v2.evaluate_agent
if exist "ayla_v2\evaluation\results" start "" "ayla_v2\evaluation\results"
pause
