"""Flask web application for bankruptcy document processing."""

import os
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import threading
import time
import re
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from processor import DocumentProcessor

app = Flask(__name__)

# CORS настройки
if os.getenv('DEBUG', 'False').lower() == 'true':
    CORS(app)  # В DEBUG режиме разрешаем все
else:
    # В production ограничиваем CORS (укажите свой домен)
    CORS(app, origins=[os.getenv('ALLOWED_ORIGIN', 'http://localhost:3000')])

# Настройки приложения
app.config['UPLOAD_FOLDER'] = Path('uploads')
app.config['OUTPUT_FOLDER'] = Path('outputs')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE', 200 * 1024 * 1024))  # По умолчанию 200MB
app.config['DATABASE'] = os.getenv('DATABASE_PATH', 'debtors.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)


def safe_print_exc():
    """Print traceback but guard against UnicodeDecodeError in traceback formatting."""
    import traceback
    try:
        traceback.print_exc()
    except Exception as te:
        # Fallback: print basic exception info
        try:
            print("[TRACEBACK] traceback.print_exc() failed:", te)
            print(traceback.format_exc())
        except Exception:
            # Last resort: print minimal message
            print("[TRACEBACK] Failed to format traceback; see logs for details.")

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(413)
def request_entity_too_large(error):
    """Обработчик ошибки превышения максимального размера запроса."""
    max_size_mb = app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
    return jsonify({
        'error': f'Файл слишком большой. Максимальный размер: {max_size_mb:.0f} MB',
        'max_size': app.config['MAX_CONTENT_LENGTH']
    }), 413

def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Включаем поддержку внешних ключей в SQLite
    cursor.execute('PRAGMA foreign_keys = ON')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debtors (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            date_added TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            raw_data TEXT DEFAULT '{}',
            lawyer TEXT DEFAULT 'urist1'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debtor_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            is_generated INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (debtor_id) REFERENCES debtors (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processing_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debtor_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            created_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            error_message TEXT,
            FOREIGN KEY (debtor_id) REFERENCES debtors (id) ON DELETE CASCADE
        )
    ''')
    
    # Добавляем колонку lawyer если её нет (для миграции старых БД)
    try:
        cursor.execute('SELECT lawyer FROM debtors LIMIT 1')
    except sqlite3.OperationalError:
        print("[MIGRATION] Adding lawyer column to debtors table")
        cursor.execute('ALTER TABLE debtors ADD COLUMN lawyer TEXT DEFAULT "urist1"')
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'], timeout=30.0)  # Увеличиваем таймаут до 30 секунд
    conn.row_factory = sqlite3.Row
    # ВАЖНО: Включаем foreign keys для каждого соединения
    conn.execute('PRAGMA foreign_keys = ON')
    # Включаем WAL mode для лучшей конкурентности
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def execute_with_retry(conn, query, params=None, max_retries=3):
    """Выполняет SQL запрос с повторными попытками при блокировке базы."""
    for attempt in range(max_retries):
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < max_retries - 1:
                print(f"[DB] Database locked, retry {attempt + 1}/{max_retries}")
                time.sleep(0.5 * (attempt + 1))  # Экспоненциальная задержка
                continue
            raise

def generate_fio_fields(fio: str, devichya_familiya: str = None) -> dict:
    """Генерирует все производные поля от ФИО через OpenAI API.
    
    Args:
        fio: Полное ФИО (Фамилия Имя Отчество)
        devichya_familiya: Девичья фамилия (если есть)
    """
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Формируем контекст о девичьей фамилии
    devichya_context = ""
    if devichya_familiya:
        devichya_context = f"""

🔴 КРИТИЧЕСКИ ВАЖНО - ДЕВИЧЬЯ ФАМИЛИЯ:
У этого человека ЕСТЬ девичья фамилия: "{devichya_familiya}"

ПРАВИЛА:
1. Поле "Фамилия" = текущая фамилия БЕЗ девичьей
2. Поле "Имя" = имя
3. Поле "Отчество" = отчество
4. Поле "Прежние_имена_фамилия_отчества" = "{devichya_familiya}"
5. Поле "ФИО" = Фамилия (Девичья_фамилия) Имя Отчество
   Пример: "Ушакова (Романовна) Валерия Сергеевна"
6. Все склонения (ФИО_рп, ФИО_дп, ФИО_вп) ТАКЖЕ должны содержать девичью фамилию в скобках!
   Примеры:
   - ФИО_рп: "Ушаковой (Романовны) Валерии Сергеевны"
   - ФИО_дп: "Ушаковой (Романовне) Валерии Сергеевне"
   - ФИО_вп: "Ушакову (Романовну) Валерию Сергеевну"
"""
    else:
        devichya_context = """

🔴 ДЕВИЧЬЕЙ ФАМИЛИИ НЕТ:
Поле "Прежние_имена_фамилия_отчества" = null
Поле "ФИО" = обычный формат "Фамилия Имя Отчество" БЕЗ скобок
"""
    
    prompt = f"""Разбери ФИО "{fio}" и верни JSON с следующими полями:
{devichya_context}

1. Фамилия - только текущая фамилия (БЕЗ девичьей)
2. Имя - только имя
3. Отчество - только отчество
4. Прежние_имена_фамилия_отчества - девичья фамилия (если есть) или null
5. ФИО - ПОЛНОЕ ФИО с девичьей фамилией в скобках (если есть) или без скобок
6. Фамилия_инициалы - формат "Иванов И.П." (БЕЗ девичьей фамилии)
7. Фамилия_инициалы_рп - формат "Иванова И.П." (родительный падеж, БЕЗ девичьей)
8. Фамилия_инициалы_дп - формат "Иванову И.П." (дательный падеж, БЕЗ девичьей)
9. ФИО_рп - полное ФИО в родительном падеже С девичьей фамилией в скобках (если есть)
10. ФИО_дп - полное ФИО в дательном падеже С девичьей фамилией в скобках (если есть)
11. ФИО_вп - полное ФИО в винительном падеже С девичьей фамилией в скобках (если есть)

Верни ТОЛЬКО JSON без комментариев и markdown форматирования.

Пример для "Ушакова Валерия Сергеевна" с девичьей фамилией "Романовна":
{{
  "Фамилия": "Ушакова",
  "Имя": "Валерия",
  "Отчество": "Сергеевна",
  "Прежние_имена_фамилия_отчества": "Романовна",
  "ФИО": "Ушакова (Романовна) Валерия Сергеевна",
  "Фамилия_инициалы": "Ушакова В.С.",
  "Фамилия_инициалы_рп": "Ушаковой В.С.",
  "Фамилия_инициалы_дп": "Ушаковой В.С.",
  "ФИО_рп": "Ушаковой (Романовны) Валерии Сергеевны",
  "ФИО_дп": "Ушаковой (Романовне) Валерии Сергеевне",
  "ФИО_вп": "Ушакову (Романовну) Валерию Сергеевну"
}}

Пример для "Иванов Иван Петрович" БЕЗ девичьей фамилии:
{{
  "Фамилия": "Иванов",
  "Имя": "Иван",
  "Отчество": "Петрович",
  "Прежние_имена_фамилия_отчества": null,
  "ФИО": "Иванов Иван Петрович",
  "Фамилия_инициалы": "Иванов И.П.",
  "Фамилия_инициалы_рп": "Иванова И.П.",
  "Фамилия_инициалы_дп": "Иванову И.П.",
  "ФИО_рп": "Иванова Ивана Петровича",
  "ФИО_дп": "Иванову Ивану Петровичу",
  "ФИО_вп": "Иванова Ивана Петровича"
}}
"""
    
    try:
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "Ты помощник для обработки русских ФИО и склонения по падежам. Отвечай только в формате JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Убираем markdown форматирование если есть
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        result = json.loads(result_text)
        print(f"[FIO_GENERATION] Successfully generated fields for: {fio}")
        return result
        
    except Exception as e:
        print(f"[FIO_GENERATION ERROR] Failed to generate fields: {e}")
        # В случае ошибки возвращаем пустые значения
        return {
            "Фамилия": "",
            "Имя": "",
            "Отчество": "",
            "Прежние_имена_фамилия_отчества": devichya_familiya,
            "ФИО": f"{fio.split()[0]} ({devichya_familiya}) {' '.join(fio.split()[1:])}" if devichya_familiya else fio,
            "Фамилия_инициалы": fio,
            "Фамилия_инициалы_рп": fio,
            "Фамилия_инициалы_дп": fio,
            "ФИО_рп": fio,
            "ФИО_дп": fio,
            "ФИО_вп": fio
        }

# Инициализация базы при старте приложения (до первого запроса)
@app.before_request
def before_request():
    if not hasattr(app, 'db_initialized'):
        init_db()
        app.db_initialized = True
        start_worker()

# Processing worker
worker_lock = threading.Lock()
worker_running = False

def processing_worker():
    """Единственный worker thread для последовательной обработки документов."""
    print("[WORKER] Processing worker started")
    
    while True:
        try:
            # Транзакционное получение и блокировка задания
            conn = get_db()
            cursor = conn.cursor()
            
            # Получаем ID следующего задания
            cursor.execute('''
                SELECT id, debtor_id FROM processing_jobs 
                WHERE status = 'queued' 
                ORDER BY created_at ASC 
                LIMIT 1
            ''')
            job_row = cursor.fetchone()
            
            if job_row:
                job_id = job_row['id']
                debtor_id = job_row['debtor_id']
                
                # Транзакционное обновление статуса (atomic claim)
                cursor.execute('''
                    UPDATE processing_jobs 
                    SET status = 'processing', started_at = ? 
                    WHERE id = ? AND status = 'queued'
                ''', (datetime.now().isoformat(), job_id))
                
                # Проверяем что мы действительно захватили задание
                if cursor.rowcount == 0:
                    # Другой worker уже взял это задание
                    conn.close()
                    continue
                
                print(f"[WORKER] Starting job {job_id} for debtor {debtor_id}")
                
                cursor.execute('''
                    UPDATE debtors 
                    SET status = 'processing' 
                    WHERE id = ?
                ''', (debtor_id,))
                
                conn.commit()
                conn.close()
                
                # Обрабатываем документы
                try:
                    process_documents_for_job(debtor_id)
                    
                    # Успешно завершено
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE processing_jobs 
                        SET status = 'completed', finished_at = ? 
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), job_id))
                    
                    cursor.execute('''
                        UPDATE debtors 
                        SET status = 'completed' 
                        WHERE id = ?
                    ''', (debtor_id,))
                    
                    conn.commit()
                    conn.close()
                    
                    print(f"[WORKER] Job {job_id} completed successfully")

                except Exception as e:
                    # Ошибка обработки
                    print(f"[WORKER] Job {job_id} failed: {e}")
                    safe_print_exc()

                    try:
                        conn = get_db()
                        execute_with_retry(conn, '''
                            UPDATE processing_jobs 
                            SET status = 'failed', finished_at = ?, error_message = ? 
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), str(e), job_id))

                        execute_with_retry(conn, '''
                            UPDATE debtors 
                            SET status = 'error' 
                            WHERE id = ?
                        ''', (debtor_id,))

                        conn.commit()
                        conn.close()
                    except Exception as db_error:
                        print(f"[ERROR] Failed to update error status: {db_error}")
                        try:
                            conn.close()
                        except:
                            pass
            else:
                # Нет заданий в очереди, ждем
                conn.close()
                time.sleep(2)
                
        except Exception as e:
            print(f"[WORKER] Worker error: {e}")
            safe_print_exc()
            time.sleep(5)

def reset_orphaned_jobs():
    """Сбрасывает застрявшие 'processing' задания обратно в 'queued' при старте."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE processing_jobs 
            SET status = 'queued', started_at = NULL 
            WHERE status = 'processing'
        ''')
        
        cursor.execute('''
            UPDATE debtors 
            SET status = 'queued' 
            WHERE status = 'processing'
        ''')
        
        reset_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if reset_count > 0:
            print(f"[WORKER] Reset {reset_count} orphaned 'processing' jobs to 'queued'")
    except Exception as e:
        print(f"[WORKER] Error resetting orphaned jobs: {e}")

def start_worker():
    """Запускает worker thread один раз."""
    global worker_running
    
    with worker_lock:
        if not worker_running:
            # Сбрасываем застрявшие задания перед запуском
            reset_orphaned_jobs()
            
            worker_running = True
            worker_thread = threading.Thread(target=processing_worker, daemon=True)
            worker_thread.start()
            print("[WORKER] Worker thread initialized")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    favicon_path = Path(__file__).parent / 'static' / 'favicon.ico'
    return send_file(favicon_path, mimetype='image/x-icon')

@app.route('/api/debtors', methods=['GET'])
def get_debtors():
    search_query = request.args.get('search', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if search_query:
        # Используем LIKE без LOWER для корректной работы с русскими буквами
        cursor.execute(
            'SELECT * FROM debtors WHERE full_name LIKE ? ORDER BY date_added DESC',
            (f'%{search_query}%',)
        )
    else:
        cursor.execute('SELECT * FROM debtors ORDER BY date_added DESC')
    
    debtors = []
    for row in cursor.fetchall():
        debtors.append({
            'id': row['id'],
            'full_name': row['full_name'],
            'date_added': row['date_added'],
            'status': row['status'],
            'lawyer': row['lawyer'] if row['lawyer'] else 'urist1'
        })
    
    conn.close()
    return jsonify(debtors)

@app.route('/api/debtors/<debtor_id>', methods=['GET'])
def get_debtor(debtor_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM debtors WHERE id = ?', (debtor_id,))
    debtor_row = cursor.fetchone()
    
    if not debtor_row:
        conn.close()
        return jsonify({'error': 'Debtor not found'}), 404
    
    cursor.execute('SELECT * FROM documents WHERE debtor_id = ?', (debtor_id,))
    docs = cursor.fetchall()
    
    documents = {
        'uploaded': [],
        'generated': []
    }
    
    for doc in docs:
        doc_info = {
            'id': doc['id'],
            'filename': doc['filename'],
            'doc_type': doc['doc_type']
        }
        
        if doc['is_generated']:
            documents['generated'].append(doc_info)
        else:
            documents['uploaded'].append(doc_info)
    
    conn.close()
    
    return jsonify({
        'id': debtor_row['id'],
        'full_name': debtor_row['full_name'],
        'date_added': debtor_row['date_added'],
        'status': debtor_row['status'],
        'lawyer': debtor_row['lawyer'] if debtor_row['lawyer'] else 'urist1',
        'documents': documents,
        'raw_data': json.loads(debtor_row['raw_data']) if debtor_row['raw_data'] else {}
    })

@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    """Получить статус очереди обработки."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Считаем задания в очереди
    cursor.execute('SELECT COUNT(*) as count FROM processing_jobs WHERE status = "queued"')
    queued_count = cursor.fetchone()['count']
    
    # Считаем обрабатываемые задания
    cursor.execute('SELECT COUNT(*) as count FROM processing_jobs WHERE status = "processing"')
    processing_count = cursor.fetchone()['count']
    
    # Получаем список заданий в очереди с позициями
    cursor.execute('''
        SELECT j.id, j.debtor_id, j.status, j.created_at, d.full_name
        FROM processing_jobs j
        LEFT JOIN debtors d ON j.debtor_id = d.id
        WHERE j.status IN ('queued', 'processing')
        ORDER BY j.created_at ASC
    ''')
    jobs = []
    for idx, row in enumerate(cursor.fetchall(), start=1):
        jobs.append({
            'job_id': row['id'],
            'debtor_id': row['debtor_id'],
            'full_name': row['full_name'],
            'status': row['status'],
            'position': idx if row['status'] == 'queued' else 0,
            'created_at': row['created_at']
        })
    
    conn.close()
    
    return jsonify({
        'queued': queued_count,
        'processing': processing_count,
        'jobs': jobs
    })

@app.route('/api/debtors/<debtor_id>/deals', methods=['GET'])
def get_debtor_deals(debtor_id):
    """Получить сделки должника за последние 3 года."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT raw_data FROM debtors WHERE id = ?', (debtor_id,))
    debtor_row = cursor.fetchone()
    conn.close()
    
    if not debtor_row or not debtor_row['raw_data']:
        return jsonify([])
    
    raw_data = json.loads(debtor_row['raw_data'])
    deals = raw_data.get('сделки', [])
    
    # Фильтруем сделки за последние 3 года
    from datetime import datetime, timedelta
    three_years_ago = datetime.now() - timedelta(days=3*365)
    
    filtered_deals = []
    for deal in deals:
        if not isinstance(deal, dict):
            continue
            
        deal_date_str = deal.get('Дата_сделки')
        if not deal_date_str:
            continue
        
        try:
            # Парсим дату в формате ДД.ММ.ГГГГ
            deal_date = datetime.strptime(deal_date_str, '%d.%m.%Y')
            if deal_date >= three_years_ago:
                filtered_deals.append(deal)
        except (ValueError, TypeError):
            # Если не удалось распарсить дату, всё равно включаем
            filtered_deals.append(deal)
    
    return jsonify(filtered_deals)

@app.route('/api/debtors/<debtor_id>', methods=['DELETE'])
def delete_debtor(debtor_id):
    import shutil
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Получаем все файлы для удаления
    cursor.execute('SELECT filepath FROM documents WHERE debtor_id = ?', (debtor_id,))
    files = cursor.fetchall()
    
    # Удаляем файлы с диска
    for file_row in files:
        filepath = Path(file_row['filepath'])
        if filepath.exists():
            try:
                filepath.unlink()
            except Exception as e:
                print(f"[WARNING] Failed to delete file {filepath}: {e}")
    
    # Удаляем должника (CASCADE автоматически удалит документы из таблицы)
    cursor.execute('DELETE FROM debtors WHERE id = ?', (debtor_id,))
    
    conn.commit()
    conn.close()
    
    # Удаляем папку с загруженными файлами
    debtor_upload_folder = app.config['UPLOAD_FOLDER'] / debtor_id
    if debtor_upload_folder.exists():
        try:
            shutil.rmtree(debtor_upload_folder)
        except Exception as e:
            print(f"[WARNING] Failed to delete upload folder {debtor_upload_folder}: {e}")
    
    # Удаляем папку с outputs
    debtor_output_folder = app.config['OUTPUT_FOLDER'] / debtor_id
    if debtor_output_folder.exists():
        try:
            shutil.rmtree(debtor_output_folder)
        except Exception as e:
            print(f"[WARNING] Failed to delete output folder {debtor_output_folder}: {e}")
    
    # Удаляем папку с результатами (resultdoc)
    from processor import OUTPUT_DIR
    debtor_result_folder = OUTPUT_DIR / debtor_id
    if debtor_result_folder.exists():
        try:
            shutil.rmtree(debtor_result_folder)
        except Exception as e:
            print(f"[WARNING] Failed to delete result folder {debtor_result_folder}: {e}")
    
    return jsonify({'success': True})

@app.route('/api/debtors/<debtor_id>/data', methods=['GET'])
def get_debtor_data(debtor_id):
    """Получить данные должника из result.json."""
    # result.json находится в outputs/, а не в resultdoc/
    result_file = app.config['OUTPUT_FOLDER'] / debtor_id / 'result.json'
    
    print(f"[GET_DATA] Checking for result.json at: {result_file}")
    
    if not result_file.exists():
        print(f"[GET_DATA] File not found: {result_file}")
        return jsonify({'error': 'Data not found'}), 404
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Normalize any LINE_BREAK placeholders to real newlines for UI
        try:
            from processor import DocumentProcessor
            data = DocumentProcessor._normalize_line_breaks(data)
        except Exception:
            pass
        print(f"[GET_DATA] Successfully loaded data, keys: {list(data.keys())[:10]}")
        return jsonify(data)
    except Exception as e:
        print(f"[GET_DATA ERROR] Failed to load data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debtors/<debtor_id>/save-data', methods=['POST'])
def save_debtor_data_only(debtor_id):
    """Сохранить данные должника БЕЗ генерации документов."""
    new_data = request.json
    if not new_data:
        return jsonify({'error': 'No data provided'}), 400
    
    result_file = app.config['OUTPUT_FOLDER'] / debtor_id / 'result.json'
    if not result_file.exists():
        return jsonify({'error': 'Data file not found'}), 404
    
    try:
        # Читаем текущие данные
        with open(result_file, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        
        # Проверяем изменение ФИО или девичьей фамилии
        fio_changed = 'ФИО' in new_data and new_data['ФИО'] != current_data.get('ФИО')
        devichya_changed = 'Девичья_фамилия' in new_data and new_data.get('Девичья_фамилия') != current_data.get('Девичья_фамилия')
        
        # Если ФИО изменилось ИЛИ появилась/изменилась девичья фамилия, генерируем все производные поля через нейронку
        if fio_changed or devichya_changed:
            # Берем актуальные значения (новые или текущие)
            fio_value = new_data.get('ФИО') or current_data.get('ФИО')
            devichya_value = new_data.get('Девичья_фамилия') or current_data.get('Девичья_фамилия')
            
            if fio_value:  # Генерируем только если есть ФИО
                print(f"[SAVE_DATA] ФИО or Девичья_фамилия changed, generating derivative fields via OpenAI...")
                print(f"[SAVE_DATA] ФИО: {fio_value}, Девичья: {devichya_value}")
                fio_fields = generate_fio_fields(fio_value, devichya_value)
                
                # Добавляем сгенерированные поля к данным для обновления
                new_data.update(fio_fields)
                print(f"[SAVE_DATA] Generated fields: {list(fio_fields.keys())}")
        
        # Обновляем только переданные поля
        current_data.update(new_data)
        
        # Normalize LINE_BREAK placeholders before saving
        try:
            from processor import DocumentProcessor
            current_data = DocumentProcessor._normalize_line_breaks(current_data)
        except Exception:
            pass

        # Normalize LINE_BREAK placeholders before saving
        try:
            from processor import DocumentProcessor
            current_data = DocumentProcessor._normalize_line_breaks(current_data)
        except Exception:
            pass

        # Сохраняем обратно
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        
        # Если ФИО изменилось, обновляем его в базе данных
        if 'ФИО' in new_data:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE debtors SET full_name = ? WHERE id = ?', (new_data['ФИО'], debtor_id))
            conn.commit()
            conn.close()
            print(f"[SAVE_DATA] Updated full_name in DB to: {new_data['ФИО']}")
        
        return jsonify({'success': True, 'message': 'Данные сохранены', 'updated_data': current_data})
    except Exception as e:
        print(f"[SAVE_DATA ERROR] {e}")
        safe_print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/debtors/<debtor_id>/data', methods=['PUT'])
def update_debtor_data(debtor_id):
    """Обновить данные должника и перегенерировать документы."""
    # result.json находится в outputs/, а не в resultdoc/
    
    # Получаем новые данные из request
    new_data = request.json
    if not new_data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Сохраняем обновленные данные в result.json
    result_file = app.config['OUTPUT_FOLDER'] / debtor_id / 'result.json'
    if not result_file.exists():
        return jsonify({'error': 'Data file not found'}), 404
    
    try:
        # Читаем текущие данные
        with open(result_file, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        
        # Обновляем только переданные поля
        current_data.update(new_data)
        
        # Сохраняем обратно
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        
        # Если ФИО изменилось, обновляем его в базе данных
        if 'ФИО' in new_data:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE debtors SET full_name = ? WHERE id = ?', (new_data['ФИО'], debtor_id))
            conn.commit()
            conn.close()
            print(f"[UPDATE_DATA] Updated full_name in DB to: {new_data['ФИО']}")
        
        # Обновляем статус должника на "processing"
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE debtors SET status = ? WHERE id = ?', ('processing', debtor_id))
        conn.commit()
        conn.close()
        
        # Запускаем перегенерацию документов
        threading.Thread(target=regenerate_documents, args=(debtor_id,), daemon=True).start()
        
        return jsonify({'success': True, 'message': 'Данные обновлены, документы генерируются'})
    except Exception as e:
        safe_print_exc()
        return jsonify({'error': str(e)}), 500

def regenerate_documents(debtor_id):
    """Перегенерировать документы на основе обновленного result.json."""
    import shutil
    from pathlib import Path
    
    try:
        print(f"[REGEN] Starting document regeneration for debtor {debtor_id}")
        
        # Получаем юриста из БД
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT lawyer FROM debtors WHERE id = ?', (debtor_id,))
        debtor_row = cursor.fetchone()
        lawyer = debtor_row['lawyer'] if debtor_row and debtor_row['lawyer'] else 'urist1'
        conn.close()
        
        # Путь к result.json (в outputs/)
        result_file = app.config['OUTPUT_FOLDER'] / debtor_id / 'result.json'
        if not result_file.exists():
            print(f"[REGEN ERROR] result.json not found for debtor {debtor_id}")
            return
        
        # Загружаем данные
        with open(result_file, 'r', encoding='utf-8') as f:
            context = json.load(f)
        
        # Определяем папку с шаблонами на основе юриста
        LAWYER_FOLDERS = {
            "urist1": "templ/urist1",
            "urist2": "templ/urist2",
            "urist3": "templ/urist3",
        }
        
        template_folder = LAWYER_FOLDERS.get(lawyer, "templ/urist1")
        template_dir = Path(template_folder)
        
        # Если папки нет, используем дефолтную
        if not template_dir.exists():
            print(f"[REGEN WARNING] Template folder {template_dir} not found, using default")
            template_dir = Path("templ/urist1")
        
        # Получаем список шаблонов
        templates = list(template_dir.glob('*.docx'))
        
        # Папка для сохранения документов (resultdoc/)
        from processor import OUTPUT_DIR
        output_dir = OUTPUT_DIR / debtor_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Удаляем старые сгенерированные документы из БД
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM documents WHERE debtor_id = ? AND is_generated = 1', (debtor_id,))
        conn.commit()
        
        # Генерируем новые документы
        for template_path in templates:
            try:
                output_path = output_dir / template_path.name
                DocumentProcessor.fill_template(template_path, output_path, context)
                
                # Добавляем в БД
                cursor.execute('''
                    INSERT INTO documents (debtor_id, filename, filepath, doc_type, is_generated)
                    VALUES (?, ?, ?, ?, 1)
                ''', (debtor_id, template_path.name, str(output_path), 'generated'))
                
                print(f"[REGEN] Generated: {template_path.name}")
            except Exception as e:
                print(f"[REGEN ERROR] Failed to generate {template_path.name}: {e}")
        
        # Обновляем статус должника на "completed"
        cursor.execute('UPDATE debtors SET status = ? WHERE id = ?', ('completed', debtor_id))
        
        conn.commit()
        conn.close()
        
        print(f"[REGEN] Completed for debtor {debtor_id}")
        
    except Exception as e:
        print(f"[REGEN ERROR] Error regenerating documents for {debtor_id}: {e}")
        safe_print_exc()
        
        # В случае ошибки устанавливаем статус error
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE debtors SET status = ? WHERE id = ?', ('error', debtor_id))
            conn.commit()
            conn.close()
        except:
            pass

@app.route('/api/upload', methods=['POST'])
def upload_documents():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    lawyer = request.form.get('lawyer', 'urist1')
    
    print(f"[UPLOAD] Получено файлов в запросе: {len(files)}")
    
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400
    
    debtor_id = str(uuid.uuid4())
    debtor_folder = app.config['UPLOAD_FOLDER'] / debtor_id
    debtor_folder.mkdir(exist_ok=True)
    
    uploaded_files = []
    skipped_files = []
    max_size = app.config['MAX_CONTENT_LENGTH']
    
    for file in files:
        if not file:
            continue
            
        if not allowed_file(file.filename):
            print(f"[UPLOAD] ✗ Пропущен (не PDF): {file.filename}")
            skipped_files.append({'filename': file.filename, 'reason': 'Не PDF файл'})
            continue
        
        filename = custom_secure_filename(file.filename)
        filepath = debtor_folder / filename
        
        try:
            # Сохраняем файл
            file.save(filepath)
            file_size = filepath.stat().st_size
            
            # Проверяем размер после сохранения
            if file_size > max_size:
                filepath.unlink()  # Удаляем слишком большой файл
                print(f"[UPLOAD] ✗ Слишком большой: {filename} ({file_size / (1024*1024):.1f} MB)")
                skipped_files.append({
                    'filename': file.filename, 
                    'reason': f'Размер {file_size / (1024*1024):.1f} MB превышает лимит {max_size / (1024*1024):.0f} MB'
                })
                continue
            
            uploaded_files.append(filepath)
            print(f"[UPLOAD] ✓ Сохранен: {filename} ({file_size / 1024:.1f} KB)")
            
        except Exception as e:
            print(f"[UPLOAD] ✗ Ошибка сохранения {filename}: {e}")
            skipped_files.append({'filename': file.filename, 'reason': str(e)})
    
    if not uploaded_files:
        error_msg = 'No valid PDF files provided'
        if skipped_files:
            error_msg += f' (пропущено файлов: {len(skipped_files)})'
        print(f"[UPLOAD] ✗ {error_msg}")
        return jsonify({'error': error_msg, 'skipped': skipped_files}), 400
    
    print(f"[UPLOAD] Успешно загружено: {len(uploaded_files)} из {len(files)} файлов")
    if skipped_files:
        print(f"[UPLOAD] Пропущено: {len(skipped_files)} файлов")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Создаем запись должника
    cursor.execute(
        'INSERT INTO debtors (id, full_name, date_added, status, raw_data, lawyer) VALUES (?, ?, ?, ?, ?, ?)',
        (debtor_id, 'В очереди...', datetime.now().isoformat(), 'queued', '{}', lawyer)
    )
    
    # Сохраняем документы
    for filepath in uploaded_files:
        cursor.execute(
            'INSERT INTO documents (debtor_id, filename, filepath, doc_type, is_generated) VALUES (?, ?, ?, ?, ?)',
            (debtor_id, filepath.name, str(filepath), 'uploaded', 0)
        )
    
    # Добавляем задание в очередь
    cursor.execute(
        'INSERT INTO processing_jobs (debtor_id, status, created_at) VALUES (?, ?, ?)',
        (debtor_id, 'queued', datetime.now().isoformat())
    )
    
    conn.commit()
    conn.close()
    
    print(f"[UPLOAD] Должник {debtor_id} добавлен в очередь обработки (файлов: {len(uploaded_files)})")
    
    return jsonify({
        'success': True,
        'debtor_id': debtor_id,
        'uploaded_count': len(uploaded_files),
        'total_count': len(files),
        'skipped': skipped_files if skipped_files else []
    })

def process_documents_for_job(debtor_id):
    """Обрабатывает документы для конкретного должника из очереди."""
    try:
        print(f"[DEBUG] Starting processing for debtor {debtor_id}")
        
        # Получаем список файлов и юриста из базы данных
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT filepath FROM documents WHERE debtor_id = ? AND is_generated = 0',
            (debtor_id,)
        )
        file_rows = cursor.fetchall()
        
        # Получаем юриста
        cursor.execute('SELECT lawyer FROM debtors WHERE id = ?', (debtor_id,))
        debtor_row = cursor.fetchone()
        lawyer = debtor_row['lawyer'] if debtor_row and debtor_row['lawyer'] else 'urist1'
        
        conn.close()
        
        pdf_files = [Path(row['filepath']) for row in file_rows]
        print(f"[DEBUG] Files to process: {[f.name for f in pdf_files]}")
        
        processor = DocumentProcessor()
        
        output_folder = app.config['OUTPUT_FOLDER'] / debtor_id
        output_folder.mkdir(exist_ok=True)
        
        output_json = output_folder / 'result.json'
        
        print(f"[DEBUG] Calling process_batch with lawyer: {lawyer}")
        results, aggregated, filled_templates = processor.process_batch(
            pdf_files,
            output_json=output_json,
            debtor_id=debtor_id,
            lawyer=lawyer
        )
        
        print(f"[DEBUG] process_batch completed. Results: {len(results)}, Aggregated keys: {list(aggregated.keys()) if aggregated else 'None'}")
        print(f"[DEBUG] Filled templates: {[t.name if t else 'None' for t in (filled_templates or [])]}")
        
        # После обработки проверяем, нужно ли сгенерировать производные поля ФИО
        if output_json.exists():
            try:
                with open(output_json, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                fio_value = result_data.get('ФИО')
                devichya_value = result_data.get('Девичья_фамилия')
                
                # Генерируем производные поля если есть ФИО и еще не сгенерированы
                if fio_value and not result_data.get('Фамилия'):
                    print(f"[POST_PROCESS] Generating derivative fields for ФИО: {fio_value}, Девичья: {devichya_value}")
                    fio_fields = generate_fio_fields(fio_value, devichya_value)
                    result_data.update(fio_fields)
                    
                    # Сохраняем обновленные данные
                    with open(output_json, 'w', encoding='utf-8') as f:
                        json.dump(result_data, f, ensure_ascii=False, indent=2)
                    print(f"[POST_PROCESS] Generated fields saved: {list(fio_fields.keys())}")
            except Exception as e:
                print(f"[POST_PROCESS ERROR] Failed to generate derivative fields: {e}")
        
        # Извлекаем ФИО - сначала из aggregated, потом из result.json
        full_name = None
        if aggregated:
            passport_data = aggregated.get('паспорт', [{}])[0]
            if passport_data and 'ФИО' in passport_data:
                full_name = passport_data['ФИО']
        
        # Если не нашли в aggregated, пробуем в result.json
        if not full_name and output_json.exists():
            try:
                with open(output_json, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                    full_name = result_data.get('ФИО')
            except Exception as e:
                print(f"[DEBUG] Failed to read result.json: {e}")
        
        # Если всё равно не нашли - используем ID как имя
        if not full_name:
            full_name = f"Должник {debtor_id[:8]}"
        
        print(f"[DEBUG] Extracted name: {full_name}")
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE debtors SET full_name = ?, raw_data = ? WHERE id = ?',
            (full_name, json.dumps(aggregated, ensure_ascii=False), debtor_id)
        )
        
        print(f"[DEBUG] Updated debtor record")
        
        if filled_templates:
            for template_path in filled_templates:
                if template_path and template_path.exists():
                    cursor.execute(
                        'INSERT INTO documents (debtor_id, filename, filepath, doc_type, is_generated) VALUES (?, ?, ?, ?, ?)',
                        (debtor_id, template_path.name, str(template_path), 'generated', 1)
                    )
                    print(f"[DEBUG] Added generated document: {template_path.name}")
        
        conn.commit()
        conn.close()
        
        print(f"[DEBUG] Processing completed successfully for debtor {debtor_id}")
        
    except Exception as e:
        print(f"[ERROR] Error processing documents for debtor {debtor_id}: {e}")
        safe_print_exc()
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE debtors SET status = ? WHERE id = ?',
                ('error', debtor_id)
            )
            conn.commit()
            conn.close()
            print(f"[DEBUG] Updated status to error for debtor {debtor_id}")
        except Exception as db_error:
            print(f"[ERROR] Failed to update error status: {db_error}")

@app.route('/api/download/<int:doc_id>')
def download_document(doc_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    doc = cursor.fetchone()
    conn.close()
    
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
    
    filepath = Path(doc['filepath'])
    if not filepath.exists():
        return jsonify({'error': 'File not found on disk'}), 404
    
    return send_file(filepath, as_attachment=True, download_name=doc['filename'])

def custom_secure_filename(filename):
    """
    Безопасное имя файла с поддержкой кириллицы и ограничением длины.
    Максимальная длина имени файла в Linux: 255 байт.
    Русские символы в UTF-8: 2 байта каждый.
    """
    # Разделяем имя и расширение
    name_parts = filename.rsplit('.', 1)
    if len(name_parts) == 2:
        base_name, extension = name_parts
    else:
        base_name = filename
        extension = ''
    
    # Удаляем запрещенные символы, оставляем русские буквы, цифры, пробелы, дефисы
    base_name = re.sub(r'[^а-яА-Яa-zA-Z0-9_.\- ]', '_', base_name)
    
    # Убираем множественные пробелы и подчеркивания
    base_name = re.sub(r'[\s_]+', '_', base_name)
    base_name = base_name.strip('_')
    
    # Ограничиваем длину базового имени (оставляем место для расширения)
    # Безопасный лимит: 100 символов (с учетом 2-байтовых UTF-8 символов = ~200 байт)
    max_base_length = 100
    if len(base_name) > max_base_length:
        # Обрезаем, но оставляем начало имени читаемым
        base_name = base_name[:max_base_length]
    
    # Собираем имя обратно
    if extension:
        return f"{base_name}.{extension}"
    return base_name

if __name__ == '__main__':
    init_db()
    
    print("\n" + "=" * 80)
    print("✅ ИНН и адреса будут получаться через RusProfile")
    print("=" * 80 + "\n")
    
    # Получаем настройки из переменных окружения
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    if debug_mode:
        print("⚠️  WARNING: Running in DEBUG mode!")
        print(f"   Server: http://{host}:{port}")
        app.run(host=host, port=port, debug=True)
    else:
        print("✅ Running in PRODUCTION mode")
        print(f"   Server: http://{host}:{port}")
        print("   Use Gunicorn or Waitress for better performance")
        app.run(host=host, port=port, debug=False)
