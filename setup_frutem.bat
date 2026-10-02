@echo off
title Instalador FrutEm - Senior Dev Assistant
echo ====================================================
echo    INSTALANDO ENTORNO PARA SISTEMA FRUTEM
echo ====================================================

:: 1. Verificar si existe Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    pause
    exit
)

:: 2. Crear entorno virtual si no existe
if not exist venv (
    echo [1/3] Creando entorno virtual venv...
    python -m venv venv
) else (
    echo [1/3] Entorno virtual ya existe.
)

:: 3. Activar y actualizar pip
echo [2/3] Actualizando instalador de paquetes...
call venv\Scripts\activate
python -m pip install --upgrade pip

:: 4. Instalar dependencias necesarias para el Sistema V79
echo [3/3] Instalando librerias (CustomTkinter, Pandas, Pillow, etc.)...
pip install customtkinter pandas pillow openpyxl reportlab mysql-connector-python

echo ====================================================
echo    INSTALACION COMPLETADA
echo    Para ejecutar el sistema usa: run_frutem.bat
echo ====================================================
pause