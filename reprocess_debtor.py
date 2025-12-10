"""Скрипт для повторной обработки одного должника"""
import sys
from pathlib import Path
from processor import DocumentProcessor

if len(sys.argv) < 2:
    print("Использование: python reprocess_debtor.py <debtor_id>")
    print("Пример: python reprocess_debtor.py b03bc916-704b-4938-9ae6-6d56cd74346a")
    sys.exit(1)

debtor_id = sys.argv[1]
uploads_dir = Path("uploads") / debtor_id
outputs_dir = Path("outputs") / debtor_id
result_json = outputs_dir / "result.json"

if not uploads_dir.exists():
    print(f"❌ Папка не найдена: {uploads_dir}")
    sys.exit(1)

print(f"🔄 Повторная обработка должника: {debtor_id}")
print(f"📁 Входная папка: {uploads_dir}")
print(f"📁 Выходная папка: {outputs_dir}")
print()

# Создаем outputs если не существует
outputs_dir.mkdir(parents=True, exist_ok=True)

# Получаем список PDF файлов
pdf_files = list(uploads_dir.glob("*.pdf"))
print(f"📄 Найдено файлов: {len(pdf_files)}")
for pdf in sorted(pdf_files):
    print(f"   - {pdf.name}")
print()

# Запускаем обработку
print("=" * 80)
print("НАЧАЛО ОБРАБОТКИ")
print("=" * 80)
print()

processor = DocumentProcessor()

try:
    # Используем process_batch как в app.py
    print(f"\n{'='*80}")
    print("ОБРАБОТКА БАТЧА")
    print("=" * 80)
    
    results, aggregated, filled_templates = processor.process_batch(
        pdf_paths=sorted(pdf_files),
        debtor_id=debtor_id,
        output_json=result_json
    )
    
    print(f"\n✅ Обработка завершена!")
    print(f"📊 Обработано файлов: {len(results)}")
    print(f"📊 Заполнено шаблонов: {len(filled_templates)}")
    print(f"💾 Результаты сохранены в: {outputs_dir}")
    
    # Показываем статистику
    if aggregated:
        credits = aggregated.get("credits", [])
        taxes = aggregated.get("taxes", [])
        print(f"\n📈 Статистика:")
        print(f"   Кредиторов: {len(credits)}")
        print(f"   Налогов: {len(taxes)}")
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
