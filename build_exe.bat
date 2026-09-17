@echo off
REM Сборка ExtractBarcodes.exe из GUI-скрипта. Запускать на Windows,
REM находясь в корневой папке проекта (там же, где лежит этот файл).

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

python build_exe.py

pause
