# Foodgram

Сервис для публикации рецептов. Пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список избранного, а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## ПС
Исправил все ошибки с тестами, результат успешного прохождения 198/198 тестов прикрепил: postman_collection/postman_test_results.json

## Технологии

- Python 3.9
- Django 3.2
- Django REST Framework
- PostgreSQL
- Docker
- Nginx
- Gunicorn

## Установка и запуск

### Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/SadJaba/foodgram-st.git
cd foodgram-st
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env в директории infra:
```
DEBUG=True
SECRET_KEY=your-secret-key
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

5. Примените миграции:
```bash
python manage.py migrate
```

6. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

7. Запустите сервер разработки:
```bash
python manage.py runserver
```

### Запуск в Docker

1. Убедитесь, что у вас установлен Docker и Docker Compose

2. Соберите и запустите контейнеры:
```bash
docker-compose up -d --build
```

3. Примените миграции:
```bash
docker-compose exec backend python manage.py migrate
```

4. Создайте суперпользователя:
```bash
docker-compose exec backend python manage.py createsuperuser
```

5. Соберите статические файлы:
```bash
docker-compose exec backend python manage.py collectstatic --no-input
```

## Автор

[SadJaba](https://github.com/SadJaba) - [foodgram-st](https://github.com/SadJaba/foodgram-st)