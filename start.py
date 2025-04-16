#!/usr/bin/env python
"""Startup script for the warehouse application"""
import os
import sys
import webbrowser
import subprocess
import time
import signal
import platform
import argparse

def open_browser():
    """Open browser after a delay"""
    time.sleep(2)
    url = "http://127.0.0.1:8000"
    webbrowser.open(url)

def setup_database():
    """Setup PostgreSQL database"""
    print("Налаштування PostgreSQL...")
    try:
        # Перевірка наявності PostgreSQL
        if platform.system() == "Windows":
            psql_check = subprocess.run(["where", "psql"], capture_output=True, text=True)
        else:
            psql_check = subprocess.run(["which", "psql"], capture_output=True, text=True)
        
        if psql_check.returncode != 0:
            print("PostgreSQL не встановлено або не знаходиться в PATH.")
            print("Будь ласка, встановіть PostgreSQL та зверніться до postgres_setup.md для інструкцій.")
            sys.exit(1)
            
        # Спроба створити базу даних, якщо вона не існує
        if platform.system() == "Windows":
            create_db = '''
            $env:PGPASSWORD="postgress"
            psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname = 'sklad_db'" | Select-String -Pattern "1 row" -Quiet
            if (-not $?) {
                psql -U postgres -c "CREATE DATABASE sklad_db"
            }
            '''
            subprocess.run(["powershell", "-Command", create_db], check=False)
        else:
            create_db = '''
            export PGPASSWORD="postgress"
            if ! psql -U postgres -lqt | cut -d \| -f 1 | grep -qw sklad_db; then
                psql -U postgres -c "CREATE DATABASE sklad_db"
            fi
            '''
            subprocess.run(["bash", "-c", create_db], check=False)
            
        print("База даних налаштована успішно.")
        return True
    except Exception as e:
        print(f"Помилка при налаштуванні бази даних: {e}")
        print("Програма потребує PostgreSQL для роботи. Неможливо продовжити без PostgreSQL.")
        sys.exit(1)

def run_server():
    """Run the Django development server"""
    # Parse command line arguments (залишаємо для майбутніх розширень)
    parser = argparse.ArgumentParser(description='Запуск серверу складського обліку')
    args = parser.parse_args()
    
    # Check if virtual environment exists
    venv_dir = "venv"
    venv_python = os.path.join(venv_dir, "Scripts", "python") if platform.system() == "Windows" else os.path.join(venv_dir, "bin", "python")
    
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
    
    # Install requirements if needed
    if os.path.exists("requirements.txt"):
        print("Installing requirements...")
        if platform.system() == "Windows":
            pip_cmd = os.path.join(venv_dir, "Scripts", "pip")
        else:
            pip_cmd = os.path.join(venv_dir, "bin", "pip")
        
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
    
    # Setup PostgreSQL (обов'язково)
    setup_database()
    
    # Run migrations
    print("Running migrations...")
    subprocess.run([venv_python, "manage.py", "migrate"], check=True)
    
    # Create superuser if none exists
    try:
        subprocess.run([venv_python, "manage.py", "createsuperuser", "--noinput", 
                        "--username=admin", "--email=admin@example.com"],
                    env={**os.environ, "DJANGO_SUPERUSER_PASSWORD": "admin"})
    except:
        print("Superuser already exists or could not be created.")
    
    # Run server
    print("Starting server...")
    open_browser()
    try:
        subprocess.run([venv_python, "manage.py", "runserver"], check=True)
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    run_server() 