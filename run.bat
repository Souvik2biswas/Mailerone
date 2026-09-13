@echo off
cd /d "%~dp0"
python Mailerone.py
if errorlevel 1 (
    "C:\Users\Souvik Biswas\AppData\Local\Python\bin\python.exe" Mailerone.py
)
pause
