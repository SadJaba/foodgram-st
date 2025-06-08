FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Добавляем путь к приложению в PYTHONPATH
ENV PYTHONPATH=/app

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"] 