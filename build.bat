@echo off
cd /d "%~dp0"

py -m pip install pyinstaller

pyinstaller --noconfirm --onefile --windowed ^
  --add-data "images;images" ^
  --add-data "config.ini;." ^
  --name "InventorySystem" ^
  dashbord.py

echo Build complete: dist\InventorySystem.exe
