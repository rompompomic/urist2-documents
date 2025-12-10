FROM python:3.11-slim

# Метаданные
LABEL maintainer="your-email@example.com"
LABEL description="Bankruptcy Documents Processing System"

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей для pdf2image
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаём необходимые директории
RUN mkdir -p uploads outputs resultdoc templ

# Переменные окружения по умолчанию
ENV DEBUG=False
ENV HOST=0.0.0.0
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Открываем порт
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')"

# Запуск через Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
