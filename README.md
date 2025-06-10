# Foodgram

Сервис для публикации рецептов. Пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список избранного, а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

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
git clone https://github.com/your-username/foodgram.git
cd foodgram
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

4. Создайте файл .env в корневой директории проекта:
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

## API Endpoints

### Аутентификация
- POST /api/users/ - регистрация нового пользователя
- POST /api/auth/token/login/ - получение токена
- POST /api/auth/token/logout/ - выход из системы

### Пользователи
- GET /api/users/ - список пользователей
- GET /api/users/{id}/ - информация о пользователе
- GET /api/users/me/ - информация о текущем пользователе
- PATCH /api/users/me/ - изменение данных пользователя
- POST /api/users/set_password/ - изменение пароля

### Рецепты
- GET /api/recipes/ - список рецептов
- POST /api/recipes/ - создание рецепта
- GET /api/recipes/{id}/ - информация о рецепте
- PATCH /api/recipes/{id}/ - изменение рецепта
- DELETE /api/recipes/{id}/ - удаление рецепта

### Подписки
- GET /api/users/subscriptions/ - список подписок
- POST /api/users/{id}/subscribe/ - подписка на пользователя
- DELETE /api/users/{id}/subscribe/ - отписка от пользователя

### Избранное
- GET /api/recipes/favorite/ - список избранных рецептов
- POST /api/recipes/{id}/favorite/ - добавление в избранное
- DELETE /api/recipes/{id}/favorite/ - удаление из избранного

### Список покупок
- GET /api/recipes/download_shopping_cart/ - скачать список покупок
- POST /api/recipes/{id}/shopping_cart/ - добавление в список покупок
- DELETE /api/recipes/{id}/shopping_cart/ - удаление из списка покупок

## Автор

Ваше имя - [GitHub](https://github.com/your-username)

