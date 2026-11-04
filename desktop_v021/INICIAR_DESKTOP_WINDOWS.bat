@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title BH Lampadas - Desktop Experimental

echo ================================================
echo   BH LAMPADAS - DESKTOP EXPERIMENTAL
 echo   Janela propria para Windows 11
 echo ================================================
 echo.
set "PYTHON_CMD=python"
python --version >nul 2>&1
if errorlevel 1 (
  py --version >nul 2>&1
  if errorlevel 1 goto sem_python
  set "PYTHON_CMD=py"
)
%PYTHON_CMD% --version
if not exist ".venv_desktop\Scripts\python.exe" (
  echo Criando ambiente Python separado...
  %PYTHON_CMD% -m venv ".venv_desktop"
  if errorlevel 1 goto erro
)
if not exist ".venv_desktop\instalado_desktop.txt" (
  echo Instalando dependencias para janela desktop - internet necessaria...
  ".venv_desktop\Scripts\python.exe" -m pip install -r "requirements_desktop.txt"
  if errorlevel 1 goto erro
  echo ok>".venv_desktop\instalado_desktop.txt"
)
echo.
echo Abrindo a janela desktop da BH Lampadas...
echo Use apenas dados ficticios. Feche a janela para encerrar.
".venv_desktop\Scripts\python.exe" desktop.py
if errorlevel 1 goto erro
goto fim
:sem_python
echo ERRO: Python nao encontrado. Execute python --version no CMD.
pause
goto fim
:erro
echo.
echo Falha ao iniciar. Confira o erro acima e envie uma captura da tela.
echo Se for erro de Edge WebView2, instale o Runtime oficial da Microsoft.
pause
:fim
endlocal
