@echo off
REM ============================================================
REM  Script de Compilação do Projeto Gerador XML Oracle
REM  Autor: ChatGPT
REM  Descrição:
REM    - Cria ambiente virtual
REM    - Instala dependências
REM    - Compila o executável com PyInstaller
REM ============================================================

echo.
echo ==========================
echo   INICIANDO COMPILACAO
echo ==========================
echo.

REM ---- 1. Cria ambiente virtual se nao existir ----
if not exist .venv (
    echo Criando ambiente virtual...
    python -m venv .venv
)

REM ---- 2. Ativa ambiente virtual ----
call .venv\Scripts\activate

REM ---- 3. Atualiza pip ----
echo.
echo Atualizando pip...
python -m pip install --upgrade pip

REM ---- 4. Instala dependências ----
echo.
echo Instalando dependências principais...
pip install pyinstaller pyqt5 python-oracledb cryptography

REM ---- 5. Remove builds anteriores ----
echo.
echo Limpando builds antigos...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM ---- 6. Compila o executável ----
echo.
echo Compilando executavel...
pyinstaller --noconfirm --onefile --windowed main.py ^
    --name "Gerador_XML_Oracle" ^
    --hidden-import cryptography ^
    --hidden-import cryptography.hazmat.backends.openssl.backend ^
    --add-data "utils;utils" ^
    --add-data "xml_screens;xml_screens"

REM ---- 7. Finaliza ----
echo.
echo ==========================
echo   COMPILACAO CONCLUIDA!
echo ==========================
echo.
echo O executavel esta em: dist\Gerador_XML_Oracle.exe
echo.
pause
