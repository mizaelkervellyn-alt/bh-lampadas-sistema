@echo off
setlocal
chcp 65001 >nul
set "APP=%~dp0app.py"
set "SCHEMA=%~dp0schema.sql"
title BH Lampadas - Prototipo UFMS

if not exist "%APP%" (
    echo.
    echo [ERRO] O arquivo app.py nao foi encontrado na mesma pasta deste iniciador.
    echo.
    echo Causa mais comum: voce abriu INICIAR_WINDOWS.bat direto do ZIP.
    echo.
    echo COMO RESOLVER:
    echo  1. Feche esta janela.
    echo  2. Clique com o botao direito no arquivo .zip.
    echo  3. Clique em Extrair Tudo.
    echo  4. Abra a pasta BH_Lampadas_Prototipo ja EXTRAIDA.
    echo  5. Execute INICIAR_WINDOWS.bat la dentro.
    echo.
    echo Nesta pasta deve existir tambem o arquivo app.py.
    echo.
    pause
    exit /b 1
)
if not exist "%SCHEMA%" (
    echo [ERRO] Falta schema.sql. Extraia TODOS os arquivos do ZIP.
    pause
    exit /b 1
)

pushd "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%APP%"
) else (
    where python >nul 2>nul
    if not errorlevel 1 (
        python "%APP%"
    ) else (
        echo [ERRO] Python nao foi encontrado. Instale Python 3.8 ou superior.
    )
)

echo.
echo O aplicativo foi encerrado ou houve um erro. Verifique as mensagens acima.
echo Pressione qualquer tecla para fechar.
pause >nul
popd
endlocal
