@echo off
REM ============================================================
REM  Script de Compilação - Gerador XML Oracle (Modo THICK)
REM  Autor: ChatGPT
REM  Descrição:
REM    - Usa o Oracle Instant Client (modo thick)
REM    - Cria ambiente virtual
REM    - Instala dependências
REM    - Gera executável com PyInstaller
REM ============================================================

echo.
echo ===============================
echo   COMPILANDO EM MODO THICK
echo ===============================
echo.

REM ---- 1. Caminho do Oracle Instant Client ----
REM >>>> ATENCAO: altere o caminho abaixo conforme o local do seu Instant Client
set ORACLE_CLIENT_PATH=C:\oracle\instantclient_19_28

if not exist "%ORACLE_CLIENT_PATH%" (
    echo ERRO: O caminho do Instant Client nao foi encontrado:
    echo %ORACLE_CLIENT_PATH%
    echo.
    echo Corrija a variavel ORACLE_CLIENT_PATH no script antes de continuar.
    pause
    exit /b
)

REM ---- 2. Cria ambiente virtual se nao existir ----
if not exist .venv (
    echo Criando ambiente virtual...
    python -m venv .venv
)

REM ---- 3. Ativa o ambiente virtual ----
call .venv\Scripts\activate

REM ---- 4. Atualiza pip ----
echo.
echo Atualizando pip...
python -m pip install --upgrade pip

REM ---- 5. Instala dependências ----
echo.
echo Instalando dependências...
pip install pyinstaller pyqt5 python-oracledb

REM ---- 6. Remove builds anteriores ----
echo.
echo Limpando builds antigos...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM ---- 7. Compila o executável ----
echo.
echo Compilando executavel modo thick...
pyinstaller --noconfirm --onefile --windowed main.py ^
    --name "Gerador_XML_Oracle_THICK" ^
    --add-data "utils;utils" ^
    --add-data "xml_screens;xml_screens" ^
    --add-binary "%ORACLE_CLIENT_PATH%/*;."

REM ---- 8. Finaliza ----
echo.
echo ==============================================
echo   COMPILACAO CONCLUIDA - MODO THICK ATIVO
echo ==============================================
echo.
echo O executavel esta em: dist\Gerador_XML_Oracle_THICK.exe
echo.
pause