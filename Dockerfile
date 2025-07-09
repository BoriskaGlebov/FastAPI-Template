# 1. Базовый образ
FROM python:3.12-slim

# 2. Установка зависимостей
RUN apt-get update && apt-get install -y curl && \
    adduser --disabled-password --gecos "" app && \
    mkdir /app && chown -R app:app /app

# 3. Установка зависимостей из requirements.txt
WORKDIR /girumed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Для работы с папкой логов
RUN mkdir -p /girumed/app/logs && chown -R app:app /girumed/app/logs
# 4. Копируем приложение
COPY . .

# 5. Меняем пользователя на app
USER app

# 6. Переменные окружения будут через .env (в .dockerignore должен быть .env)
ENV PYTHONUNBUFFERED=1

# 7. Healthcheck
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

# 8. Команда запуска uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
