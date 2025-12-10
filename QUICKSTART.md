# 🚀 Быстрый старт

## Windows - Локальный запуск

### 1. Development (режим разработки)
```cmd
start-dev.bat
```
- Автоматически создаст .env из примера
- Установит зависимости
- Запустит сервер на http://localhost:5000
- DEBUG режим с автоперезагрузкой

### 2. Production (продакшн)
```cmd
start-production.bat
```
- Проверит наличие .env
- Запустит через Waitress (production WSGI сервер)
- Сервер на http://localhost:5000

## Docker - Контейнерный запуск

### 1. Сборка и запуск
```bash
# Создайте .env файл
copy .env.example .env

# Отредактируйте .env и укажите:
# - OPENAI_API_KEY=your-key
# - SECRET_KEY=random-secret
# - DEBUG=False

# Запуск
docker-compose up -d
```

### 2. Остановка
```bash
docker-compose down
```

### 3. Просмотр логов
```bash
docker-compose logs -f
```

## Linux/Mac - Production

### Через Gunicorn
```bash
# Установка
pip install -r requirements.txt

# Настройка .env
cp .env.example .env
nano .env  # отредактируйте

# Запуск
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 300 wsgi:app
```

### Через systemd (автозапуск)

Создайте `/etc/systemd/system/urist-documents.service`:

```ini
[Unit]
Description=Urist Documents Processing
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/urist-documents
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 300 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl enable urist-documents
sudo systemctl start urist-documents
sudo systemctl status urist-documents
```

## ⚙️ Настройка .env

Обязательные параметры:

```env
DEBUG=False                          # True только для разработки!
OPENAI_API_KEY=sk-...               # Ваш API ключ OpenAI
SECRET_KEY=random-secret-key-here    # Генерируйте: python -c "import secrets; print(secrets.token_hex(32))"
```

Опциональные:
```env
HOST=0.0.0.0
PORT=5000
ALLOWED_ORIGIN=https://yourdomain.com
MAX_FILE_SIZE=52428800
```

## 🔐 Безопасность

1. **Генерация SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Проверьте .env**:
   - ✅ DEBUG=False
   - ✅ Случайный SECRET_KEY
   - ✅ Действующий OPENAI_API_KEY

3. **Для production обязательно**:
   - Используйте HTTPS (Nginx/Apache reverse proxy)
   - Ограничьте CORS в ALLOWED_ORIGIN
   - Регулярно обновляйте зависимости

## 📝 Использование

1. Откройте http://localhost:5000
2. Загрузите PDF документы
3. Дождитесь обработки
4. Скачайте заполненные Word документы

## 🆘 Проблемы?

### Порт занят
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

### Ошибка OPENAI_API_KEY
Проверьте:
- Ключ действителен
- Ключ правильно указан в .env
- На счету есть баланс

### Ошибки импорта
```bash
pip install -r requirements.txt --upgrade
```

---

**Готово!** Приложение настроено для production 🎉
