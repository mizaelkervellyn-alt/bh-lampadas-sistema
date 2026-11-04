@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv_desktop\Scripts\python.exe" (
 echo Inicie antes o arquivo INICIAR_DESKTOP_WINDOWS.bat para instalar as dependencias.
 pause
 exit /b 1
)
echo Executando verificacoes de recursos, armazenamento e servidor...
".venv_desktop\Scripts\python.exe" -m unittest -v testes_desktop.py
if errorlevel 1 goto erro
echo.
echo Verificacoes concluidas com sucesso.
pause
exit /b 0
:erro
echo Houve falha em uma ou mais verificacoes. Envie uma captura.
pause
exit /b 1
