@echo off
echo Starting Admin Portal...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Make migrations
echo Creating migrations...
python manage.py makemigrations

REM Apply migrations
echo Applying migrations...
python manage.py migrate

REM Create superuser (skip if already exists)
echo.
echo Create admin user (if not already exists)
python manage.py createsuperuser

REM Run server
echo.
echo Starting server at http://localhost:8001
echo Admin portal URL: http://localhost:8001/admin/portal/
echo Login URL: http://localhost:8001/admin/login/
echo.
python manage.py runserver 8001