@echo off
python -m unittest discover -s tests -p "test*.py"
if errorlevel 1 pause & exit /b 1
python app.py
pause
