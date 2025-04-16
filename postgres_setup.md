# Налаштування PostgreSQL для проекту складського обліку

## Вимоги

**ВАЖЛИВО: Ця програма працює ВИКЛЮЧНО з PostgreSQL і не підтримує SQLite!**

## Встановлення PostgreSQL

### Windows
1. Завантажте PostgreSQL з офіційного сайту: https://www.postgresql.org/download/windows/
2. Запустіть інсталятор та виконайте встановлення
3. Запам'ятайте пароль для користувача postgres
4. Встановіть порт 5432 (за замовчуванням)
5. Після встановлення переконайтесь, що сервіс PostgreSQL запущено

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS
```bash
brew install postgresql
brew services start postgresql
```

## Перевірка встановлення

```bash
# Windows
where psql

# Linux/macOS
which psql
```

Якщо команда повертає шлях до виконуваного файлу psql, значить PostgreSQL встановлено правильно.

## Створення бази даних

### Windows
1. Відкрийте pgAdmin (встановлюється разом з PostgreSQL)
2. Підключіться до локального сервера
3. Створіть нову базу даних з назвою "sklad_db"

### Використання командного рядка (всі ОС)
```bash
# Підключення до PostgreSQL
psql -U postgres

# Створення бази даних
CREATE DATABASE sklad_db;

# Вихід
\q
```

## Налаштування користувача і паролю

За замовчуванням проект використовує такі налаштування підключення:
- Ім'я бази даних: `sklad_db`
- Користувач: `postgres`
- Пароль: `postgress`
- Хост: `localhost`
- Порт: `5432`

Якщо ви використовуєте інші налаштування, відредагуйте файл `sklad_app/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sklad_db',  # Змініть на вашу назву бази даних
        'USER': 'postgres',  # Змініть на вашого користувача
        'PASSWORD': 'postgress',  # Змініть на ваш пароль
        'HOST': 'localhost',  # Змініть, якщо PostgreSQL на іншому сервері
        'PORT': '5432',  # Змініть, якщо порт інший
    }
}
```

## Перевірка підключення

Запустіть скрипт перевірки підключення:
```bash
python test_db_connection.py
```

Якщо з'єднання успішне, ви побачите відповідне повідомлення та версію PostgreSQL.

## Виконання міграцій

Після налаштування бази даних виконайте міграції:
```bash
python manage.py migrate
```

## Запуск сервера

Після успішного налаштування PostgreSQL та виконання міграцій, запустіть сервер:
```bash
python manage.py runserver
```

## Можливі проблеми та їх вирішення

### 1. Проблема підключення до PostgreSQL

**Помилка**: "could not connect to server: Connection refused"

**Вирішення**:
- Переконайтеся, що сервіс PostgreSQL запущено
- Перевірте, що PostgreSQL слухає на порту 5432 (або вказаному вами)
- Перевірте налаштування firewall

### 2. Проблема з автентифікацією

**Помилка**: "password authentication failed for user"

**Вирішення**:
- Перевірте правильність пароля в налаштуваннях
- Перевірте права доступу користувача до бази даних

### 3. База даних не існує

**Помилка**: "database does not exist"

**Вирішення**:
- Створіть базу даних з необхідною назвою
- Перевірте правильність назви бази даних в налаштуваннях

### 4. psql не знайдено

**Помилка**: "psql не знайдено" або "command not found"

**Вирішення**:
- Переконайтеся, що PostgreSQL встановлено
- Додайте шлях до PostgreSQL у змінну PATH вашої системи
