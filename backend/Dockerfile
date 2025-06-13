FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы
COPY . .

# Создаем директорию data
RUN mkdir -p /app/data

# Добавляем путь к приложению в PYTHONPATH
ENV PYTHONPATH=/app

# Используем CMD вместо ENTRYPOINT
CMD ["sh", "-c", "python manage.py makemigrations api --noinput && \
                  python manage.py migrate --noinput && \
                  python manage.py collectstatic --noinput && \
                  python manage.py createsuperuser --noinput --username admin --email admin@example.com || true && \
                  python manage.py load_ingredients && \
                  gunicorn config.wsgi:application --bind 0.0.0.0:8000"] 