@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title BH Lampadas - Modulo 2

echo ==================================================
echo  BH LAMPADAS - MODULO 2 - VERSAO LOCAL DE TESTE
echo ==================================================
echo.
echo Verificando Python...
set "PYTHON_CMD=python"
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 goto sem_python
    set "PYTHON_CMD=py"
)
%PYTHON_CMD% --version

echo.
echo Verificando ambiente separado do projeto...
if not exist ".venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv ".venv"
    if errorlevel 1 goto erro
)

if not exist ".venv\instalacao_concluida.txt" (
    echo.
    echo Instalando dependencias pela primeira vez. Internet necessaria.
    ".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
    if errorlevel 1 goto erro
    echo Dependencias instaladas > ".venv\instalacao_concluida.txt"
)

echo.
echo Iniciando sistema em http://127.0.0.1:8766
echo Para encerrar, pressione Ctrl+C nesta janela.
echo.
".venv\Scripts\python.exe" -m uvicorn app_modulo2:app --host 127.0.0.1 --port 8766
if errorlevel 1 goto erro
goto fim

:sem_python
echo ERRO: Python nao foi encontrado no PATH.
echo Confira instalacao e execute python --version no CMD.
pause
goto fim

:erro
echo.
echo Nao foi possivel iniciar a aplicacao.
echo Se houver mensagem de erro acima, envie uma captura dela.
pause

:fim
endlocal
