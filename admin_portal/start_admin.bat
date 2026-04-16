@echo off
REM Activate virtual environment
call venv\Scripts\activate

REM Run migrations
python manage.py makemigrations
python manage.py migrate

REM Start server
python manage.py runserver 8001