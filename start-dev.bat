@echo off
REM ============================================
REM Скрипт запуска в DEVELOPMENT режиме (Windows)
REM ============================================

echo ========================================
echo   Urist Documents - Development Start
echo ========================================
echo.

REM Проверка наличия .env файла
if not exist .env (
    echo [WARNING] Файл .env не найден. Создаём из примера...
    copy .env.example .env
    echo.
    echo [ACTION REQUIRED] Отредактируйте .env файл и укажите:
    echo   - OPENAI_API_KEY=your-api-key
    echo   - DEBUG=True
    echo.
    pause
)

echo [OK] Файл .env найден
echo.

REM Проверка установки зависимостей
echo Проверка зависимостей...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [WARNING] Зависимости не установлены!
    echo.
    echo Устанавливаем...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Ошибка установки!
        pause
        exit /b 1
    )
)

echo [OK] Зависимости установлены
echo.

REM Запуск в режиме разработки
echo Запуск в режиме DEVELOPMENT...
echo.
echo Сервер: http://localhost:5000
echo Режим: DEBUG (автоперезагрузка при изменениях)
echo.
echo Для остановки нажмите Ctrl+C
echo.
echo ========================================
echo.

python app.py
