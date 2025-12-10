# 🚀 Развертывание на Ubuntu VPS

## Шаг 1: Подключение к серверу

```bash
ssh root@ваш_ip_адрес
# или
ssh username@ваш_ip_адрес
```

## Шаг 2: Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

## Шаг 3: Установка Git

```bash
sudo apt install git -y
```

## Шаг 4: Удаление старого Docker (если установлен)

```bash
# Останавливаем все контейнеры
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || true

# Удаляем старый Docker
sudo apt remove docker docker-engine docker.io containerd runc -y
sudo apt autoremove -y
```

## Шаг 5: Установка нового Docker

```bash
# Установка зависимостей
sudo apt install ca-certificates curl gnupg lsb-release -y

# Добавление официального GPG ключа Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Добавление репозитория Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker Engine
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# Проверка установки
sudo docker --version
sudo docker compose version
```

## Шаг 6: Добавление пользователя в группу docker (опционально)

```bash
sudo usermod -aG docker $USER
newgrp docker
# Или перелогиньтесь: exit и снова ssh
```

## Шаг 7: Клонирование проекта

```bash
# Переход в домашнюю директорию
cd ~

# Клонирование репозитория
git clone https://github.com/rompompomic/urist2-documents.git
cd urist2-documents
```

## Шаг 8: Настройка переменных окружения

```bash
# Создание .env файла
nano .env
```

Вставьте следующее содержимое (замените на ваши данные):

```env
# OpenAI API
OPENAI_API_KEY=sk-your-actual-api-key-here

# Flask settings
FLASK_ENV=production
SECRET_KEY=your-secret-key-generate-random-string
DEBUG=False

# Server settings
HOST=0.0.0.0
PORT=5000

# Optional: Database settings if needed
# DATABASE_URL=sqlite:///debtors.db
```

Сохраните файл: `Ctrl+O`, `Enter`, `Ctrl+X`

## Шаг 9: Создание необходимых директорий

```bash
mkdir -p uploads outputs resultdoc templ cbr_data
chmod 755 uploads outputs resultdoc templ cbr_data
```

## Шаг 10: Сборка и запуск Docker контейнера

```bash
# Сборка образа
sudo docker compose build

# Запуск в фоновом режиме
sudo docker compose up -d

# Проверка статуса
sudo docker compose ps

# Просмотр логов
sudo docker compose logs -f
```

## Шаг 11: Проверка работы сервиса

```bash
# Проверка локально на сервере
curl http://localhost:5000

# Проверка с вашего компьютера (замените IP)
curl http://ваш_ip_адрес:5000
```

## Шаг 12: Настройка файрвола (UFW)

```bash
# Установка UFW (если не установлен)
sudo apt install ufw -y

# Разрешаем SSH (ВАЖНО! Иначе потеряете доступ)
sudo ufw allow OpenSSH
sudo ufw allow 22/tcp

# Разрешаем порт приложения
sudo ufw allow 5000/tcp

# Включаем файрвол
sudo ufw enable

# Проверка статуса
sudo ufw status
```

## Шаг 13: Настройка автозапуска

Docker Compose автоматически настроен на перезапуск (`restart: unless-stopped` в docker-compose.yml)

Проверка:
```bash
# Перезагрузка сервера
sudo reboot

# После перезагрузки проверьте
sudo docker compose ps
```

---

## 📋 Полезные команды

### Управление контейнерами

```bash
# Просмотр логов
sudo docker compose logs -f

# Перезапуск
sudo docker compose restart

# Остановка
sudo docker compose down

# Остановка и удаление томов
sudo docker compose down -v

# Пересборка после изменений
sudo docker compose up -d --build
```

### Обновление кода

```bash
cd ~/urist2-documents
git pull origin main
sudo docker compose up -d --build
```

### Просмотр статуса

```bash
# Статус контейнеров
sudo docker compose ps

# Использование ресурсов
sudo docker stats

# Логи последних 100 строк
sudo docker compose logs --tail=100
```

### Очистка

```bash
# Удаление неиспользуемых образов
sudo docker image prune -a

# Удаление неиспользуемых томов
sudo docker volume prune

# Полная очистка
sudo docker system prune -a --volumes
```

---

## 🔧 Настройка Nginx (опционально, для домена и HTTPS)

### 1. Установка Nginx

```bash
sudo apt install nginx -y
```

### 2. Создание конфигурации

```bash
sudo nano /etc/nginx/sites-available/urist-app
```

Вставьте:

```nginx
server {
    listen 80;
    server_name ваш_домен.ru www.ваш_домен.ru;

    client_max_body_size 50M;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

### 3. Активация конфигурации

```bash
sudo ln -s /etc/nginx/sites-available/urist-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Настройка HTTPS с Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d ваш_домен.ru -d www.ваш_домен.ru
```

### 5. Обновление файрвола

```bash
sudo ufw allow 'Nginx Full'
sudo ufw delete allow 5000/tcp
sudo ufw status
```

---

## 🛡️ Безопасность

### 1. Создание нового пользователя (вместо root)

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
sudo usermod -aG docker deploy
```

### 2. Настройка SSH ключей

На вашем компьютере:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
ssh-copy-id deploy@ваш_ip_адрес
```

### 3. Отключение root логина

```bash
sudo nano /etc/ssh/sshd_config
```

Измените:
```
PermitRootLogin no
PasswordAuthentication no
```

```bash
sudo systemctl restart sshd
```

---

## 📊 Мониторинг

### Установка htop

```bash
sudo apt install htop -y
htop
```

### Просмотр логов системы

```bash
# Логи Docker
sudo journalctl -u docker -f

# Логи приложения
sudo docker compose logs -f --tail=100
```

### Проверка дискового пространства

```bash
df -h
du -sh ~/urist2-documents/*
```

---

## ❗ Решение проблем

### Контейнер не запускается

```bash
# Просмотр ошибок
sudo docker compose logs

# Проверка портов
sudo netstat -tulpn | grep 5000
sudo lsof -i :5000
```

### Нет места на диске

```bash
# Очистка Docker
sudo docker system prune -a --volumes

# Очистка логов
sudo journalctl --vacuum-time=7d
```

### Приложение недоступно

```bash
# Проверка файрвола
sudo ufw status

# Проверка Nginx (если используется)
sudo nginx -t
sudo systemctl status nginx

# Проверка контейнера
sudo docker compose ps
curl http://localhost:5000
```

### Ошибка API ключа

```bash
# Проверьте .env файл
cat .env | grep OPENAI

# Перезапустите контейнер
sudo docker compose restart
```

---

## 🔄 Быстрый старт (TL;DR)

```bash
# 1. Подключение
ssh root@ваш_ip

# 2. Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install docker-compose-plugin -y

# 3. Клонирование и настройка
git clone https://github.com/rompompomic/urist2-documents.git
cd urist2-documents
nano .env  # Добавьте OPENAI_API_KEY

# 4. Запуск
sudo docker compose up -d

# 5. Настройка файрвола
sudo apt install ufw -y
sudo ufw allow OpenSSH
sudo ufw allow 5000/tcp
sudo ufw enable

# 6. Проверка
curl http://localhost:5000
```

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `sudo docker compose logs`
2. Проверьте статус: `sudo docker compose ps`
3. Проверьте переменные окружения: `cat .env`
4. Проверьте подключение: `curl http://localhost:5000`
