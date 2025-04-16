#!/usr/bin/env python
"""
Скрипт для тестування підключення до бази даних PostgreSQL.
"""
import os
import sys
import psycopg2
from psycopg2 import OperationalError

# Налаштування бази даних
DB_NAME = "sklad_db"
DB_USER = "postgres"
DB_PASSWORD = "postgress"
DB_HOST = "localhost"
DB_PORT = "5432"

def test_connection():
    """Перевірка підключення до бази даних PostgreSQL."""
    connection = None
    try:
        # Підключення до бази даних
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        
        # Перевірка підключення
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print("🟢 Успішне підключення до PostgreSQL!")
        print(f"Version: {db_version[0]}")
        return True
    
    except OperationalError as error:
        print("🔴 Помилка підключення до PostgreSQL!")
        print(f"Помилка: {error}")
        print("Перевірте, чи встановлено PostgreSQL та чи запущено сервер.")
        print("Ця програма працює ТІЛЬКИ з PostgreSQL!")
        return False
    
    finally:
        # Закриваємо підключення
        if connection:
            connection.close()

def create_database():
    """Спроба створити базу даних, якщо вона не існує."""
    try:
        # Підключення до сервера PostgreSQL без вказання конкретної бази даних
        connection = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        connection.autocommit = True
        cursor = connection.cursor()
        
        # Перевірка існування бази даних
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Створення бази даних {DB_NAME}...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"База даних {DB_NAME} успішно створена.")
        else:
            print(f"База даних {DB_NAME} вже існує.")
        
        return True
    
    except OperationalError as error:
        print("🔴 Помилка підключення до PostgreSQL!")
        print(f"Помилка: {error}")
        print("\nПерегляньте інструкції з налаштування PostgreSQL у файлі postgres_setup.md")
        print("Ця програма працює ТІЛЬКИ з PostgreSQL!")
        return False
    
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    print("=== Тестування підключення до PostgreSQL ===")
    
    # Спочатку перевіряємо підключення до існуючої бази даних
    if not test_connection():
        # Якщо підключення невдале, спробуємо створити базу даних
        print("\nСпроба створити базу даних...")
        if create_database():
            # Повторне тестування підключення
            print("\nПовторне тестування підключення...")
            if test_connection():
                print("\nВиконати Django міграції? (y/n)")
                choice = input().lower()
                
                if choice == 'y':
                    print("Виконуємо міграції Django...")
                    os.system("python manage.py migrate")
                    print("Міграції виконано.")
        else:
            print("\nНЕМОЖЛИВО ПРОДОВЖИТИ БЕЗ POSTGRESQL!")
            sys.exit(1)
    else:
        print("\nВиконати Django міграції? (y/n)")
        choice = input().lower()
        
        if choice == 'y':
            print("Виконуємо міграції Django...")
            os.system("python manage.py migrate")
            print("Міграції виконано.") 