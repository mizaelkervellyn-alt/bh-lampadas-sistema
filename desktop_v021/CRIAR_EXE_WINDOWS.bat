@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title BH Lampadas - Gerar Executavel
if not exist ".venv_desktop\Scripts\python.exe" (
  echo Primeiro rode INICIAR_DESKTOP_WINDOWS.bat para instalar as dependencias.
  pause
  exit /b 1
)
echo Instalando PyInstaller para criar EXE no proprio Windows...
".venv_desktop\Scripts\python.exe" -m pip install "pyinstaller==6.8.0"
if errorlevel 1 goto erro
".venv_desktop\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed ^
 --name BH_Lampadas_Desktop ^
 --paths "modulo2" ^
 --add-data "modulo2;modulo2" ^
 --collect-all webview ^
 --hidden-import clr ^
 desktop.py
if errorlevel 1 goto erro
echo.
echo Executavel gerado em dist\BH_Lampadas_Desktop\BH_Lampadas_Desktop.exe
echo IMPORTANTE: leve a pasta inteira dist\BH_Lampadas_Desktop; nao apenas o exe.
start "" "dist\BH_Lampadas_Desktop"
pause
exit /b 0
:erro
echo Nao foi possivel gerar EXE. Envie captura da mensagem de erro.
pause
exit /b 1
