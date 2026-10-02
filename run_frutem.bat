@echo off
cd /d "%~dp0"
call venv\Scripts\activate
echo Iniciando Sistema FrutEm...
python main.py
pause