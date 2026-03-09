@echo off
REM Activate venv and initialize database

cd /d "c:\Users\DESMOND\Desktop\cali clear\ecommerce-site\backend"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Initialize database
echo Creating database and admin user...
python init_database.py

echo.
echo Checking if database was created...
dir *.db 2>nul || echo No database file found

REM Start Flask app
echo.
echo Starting Flask backend on http://localhost:5000
echo Press Ctrl+C to stop the server
python app.py
