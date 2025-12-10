@echo off
REM ============================================
REM Скрипт запуска в PRODUCTION режиме (Windows)
REM ============================================

echo ========================================
echo   Urist Documents - Production Start
echo ========================================
echo.

REM Проверка наличия .env файла
if not exist .env (
    echo [ERROR] Файл .env не найден!
    echo.
    echo Создайте .env файл из .env.example:
    echo   copy .env.example .env
    echo.
    echo Затем отредактируйте .env и укажите:
    echo   - OPENAI_API_KEY
    echo   - SECRET_KEY
    echo   - DEBUG=False
    echo.
    pause
    exit /b 1
)

echo [OK] Файл .env найден
echo.

REM Проверка установки зависимостей
echo Проверка зависимостей...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [WARNING] Flask не установлен!
    echo.
    echo Устанавливаем зависимости...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Ошибка установки зависимостей!
        pause
        exit /b 1
    )
)

echo [OK] Зависимости установлены
echo.

REM Запуск через Waitress (рекомендуется для Windows)
echo Запуск сервера через Waitress...
echo.
echo Сервер будет доступен на: http://localhost:5000
echo.
echo Для остановки нажмите Ctrl+C
echo.
echo ========================================
echo.

waitress-serve --host=127.0.0.1 --port=8000 --threads=4 --channel-timeout=300 wsgi:app
