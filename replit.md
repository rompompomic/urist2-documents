# Система автоматизации банкротных заявлений

## Описание проекта
Flask-приложение для автоматической обработки документов и заполнения форм для банкротных дел. Использует OpenAI GPT-5 Vision API для извлечения данных из отсканированных документов (паспорта, ИНН, СНИЛС, трудовые книжки, выписки ЕГРН, кредитные отчёты) и автоматического заполнения шаблонов заявлений в формате DOCX.

## Технический стек
- **Backend**: Flask 3.0.0 + Gunicorn (production WSGI)
- **AI/ML**: OpenAI GPT-5 Vision API (для OCR и извлечения данных)
- **PDF обработка**: pypdfium2 5.0.0 (чистый Python, без системных зависимостей)
- **Обработка DOCX**: python-docx, docxtpl (для шаблонизации)
- **Изображения**: Pillow 10.0.0
- **Утилиты**: num2words (суммы прописью)

## Архитектура

### Структура проекта
```
/
├── app.py                 # Flask веб-сервер (REST API + UI)
├── processor.py           # Ядро обработки документов (DocumentProcessor)
├── wsgi.py               # Gunicorn entry point для production
├── requirements.txt      # Python зависимости
├── templ/                # Шаблоны DOCX для заполнения
├── resultdoc/            # Готовые заполненные документы
├── static/               # CSS, JS для веб-интерфейса
└── templates/            # HTML шаблоны (Jinja2)
```

### Workflow обработки документов
1. **Загрузка PDF** → Конвертация в изображения (pypdfium2)
2. **Vision API** → Распознавание текста + извлечение структурированных данных (GPT-5)
3. **Агрегация** → Объединение данных из всех документов должника
4. **Заполнение** → Генерация DOCX из шаблона с динамическими таблицами
5. **Экспорт** → ZIP архив с готовыми документами

## Последние изменения

### 10 ноября 2025 - Система очередей обработки
**Задача**: Реализовать последовательную обработку документов (по одному пакету за раз)

**Решение**: Добавлена система очередей с персистентностью
- ✅ Таблица `processing_jobs` в SQLite для хранения очереди
- ✅ Один worker thread обрабатывает задания последовательно
- ✅ Transactional job claiming (предотвращает race conditions)
- ✅ Восстановление застрявших заданий после перезапуска
- ✅ API endpoint `/api/queue/status` для мониторинга
- ✅ Frontend показывает позицию каждого должника в очереди

**Архитектура очереди**:
```python
# Worker thread (один на приложение)
def processing_worker():
    while True:
        # Получаем следующее задание (transactional)
        job = SELECT FROM processing_jobs WHERE status='queued' LIMIT 1
        UPDATE processing_jobs SET status='processing' WHERE id=job_id AND status='queued'
        
        # Обрабатываем
        process_documents_for_job(debtor_id)
        
        # Обновляем статус
        UPDATE processing_jobs SET status='completed'
```

**UI показывает**:
- Баннер очереди: "Обрабатывается: 1 • В очереди: 3"
- Позиция каждого должника: "В очереди (#1)", "В очереди (#2)", "Обрабатывается"

### 8 ноября 2025 - Миграция на pypdfium2
**Проблема**: pdf2image требует системную утилиту `poppler-utils`, которая:
- Недоступна через Nix modules в Replit
- Сложно подключать из `/nix/store` (нестабильные пути между dev/production)
- Autoscale deployment не поддерживает `nix-shell` для подключения зависимостей

**Решение**: Заменили `pdf2image` → `pypdfium2`
- ✅ Чистая Python библиотека (нет системных зависимостей)
- ✅ Встроенная библиотека PDFium (Google Chromium project)
- ✅ Работает одинаково в dev и production
- ✅ Простая установка через pip

**Изменения в коде**:
```python
# Было (pdf2image + poppler):
from pdf2image import convert_from_path
images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)

# Стало (pypdfium2):
import pypdfium2 as pdfium
pdf = pdfium.PdfDocument(str(pdf_path))
for i in range(len(pdf)):
    page = pdf[i]
    bitmap = page.render(scale=2.0)  # 150 DPI
    image = bitmap.to_pil()
```

### 8 ноября 2025 - Переход на VM deployment
**Проблема**: Autoscale deployment удаляет файловую систему при каждом перезапуске:
- Загруженные PDF (`uploads/`) исчезают
- База данных SQLite (`debtors.db`) сбрасывается
- Готовые документы (`resultdoc/`) теряются

**Решение**: Переключились на **VM deployment**
- ✅ Постоянная файловая система (файлы сохраняются навсегда)
- ✅ Сервер работает 24/7 (не останавливается между запросами)
- ✅ SQLite база данных сохраняется между перезапусками
- ✅ Все загруженные и сгенерированные файлы остаются на диске

### Конфигурация deployment
- **Development**: `python app.py` (Flask dev server, 0.0.0.0:5000)
- **Production**: `gunicorn wsgi:app --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120`
- **Deployment type**: **VM** (постоянный контейнер, файлы сохраняются)

## OpenAI API Configuration
- **Модель**: `gpt-5` (требуется доступ к GPT-5 Preview)
- **API ключ**: `OPENAI_API_KEY` (environment secret)
- **Лимиты**: Проверить квоту на https://platform.openai.com/usage
- **Обработка**: Асинхронная (daemon threads), детальное логирование

## Известные проблемы
1. **OpenAI API quota exceeded (429)** → Пополнить баланс OpenAI аккаунта
2. **LSP type hints warnings** → Не влияют на работу, можно игнорировать
3. **Browser 404 ошибки** → Проверить пути к статическим файлам (не критично)

## Запуск и тестирование

### Development (локально)
```bash
python app.py
# Откройте: http://localhost:5000
```

### Production (Replit deployment)
1. Нажмите **Deploy** в Replit UI
2. Проверьте логи deployment на наличие ошибок
3. Тестируйте на production URL

### Тестирование обработки
1. Нажмите "+ Добавить должника"
2. Загрузите PDF документы (паспорт, ИНН, СНИЛС и т.д.)
3. Нажмите "Обработать" и дождитесь завершения
4. Скачайте ZIP с заполненными формами

## User Preferences
- **Язык**: Русский (документы РФ, UI на русском)
- **Модель AI**: GPT-5 (обязательно)
- **Стиль кода**: Type hints, docstrings, понятные комментарии
- **Логирование**: Подробное (для debugging асинхронной обработки)

## Полезные команды
```bash
# Установка зависимостей
pip install -r requirements.txt

# Проверка OpenAI ключа
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OK' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"

# Перезапуск сервера
# (автоматически при изменении кода в Replit)
```

## Архитектурные решения
- **Асинхронная обработка**: Daemon threads для background tasks (не блокирует UI)
- **Stateless design**: Хранение данных в JSON файлах (совместимо с autoscale)
- **Error resilience**: Fallback стратегии для OCR ошибок
- **Динамические таблицы**: docxtpl для сложных DOCX шаблонов с переменным числом строк
