"""WSGI entry point for production deployment."""

import os
from app import app, init_db

# Инициализируем БД при старте (только один раз при импорте модуля)
init_db()

# Для Gunicorn: экспортируем app на уровне модуля
application = app

if __name__ == "__main__":
    # Для прямого запуска (не рекомендуется в production)
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
