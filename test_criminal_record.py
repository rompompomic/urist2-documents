"""
Тестовый скрипт для проверки обработки справки о судимости.
"""

from processor import DocumentProcessor
from pathlib import Path
import json

# Путь к справке о судимости
pdf_path = Path("uploads/dabfc5c9-7160-4359-8f0c-81d87e22a0dd/Справка_об_отсутствии_судимости.pdf")

if pdf_path.exists():
    print(f"✓ Найден файл: {pdf_path}")
    
    # Создаём процессор
    processor = DocumentProcessor()
    
    # Пытаемся определить тип документа
    doc_type = processor.detect_document_type(pdf_path.name)
    print(f"✓ Определён тип документа: {doc_type}")
    
    # Обрабатываем документ
    print(f"\nОбработка документа...")
    result = processor.process_pdf(pdf_path)
    
    print(f"\n✓ Результат обработки:")
    print(f"  - Тип: {result.document_type}")
    print(f"  - Данные: {json.dumps(result.data, ensure_ascii=False, indent=2)}")
    
    # Проверяем наличие девичьей фамилии
    if "Девичья_фамилия" in result.data:
        print(f"\n✅ Девичья_фамилия: {result.data['Девичья_фамилия']}")
    else:
        print(f"\n⚠️ Поле Девичья_фамилия отсутствует")
        
    # Проверяем ФИО
    if "ФИО" in result.data:
        print(f"✅ ФИО: {result.data['ФИО']}")
    else:
        print(f"⚠️ Поле ФИО отсутствует")
        
else:
    print(f"❌ Файл не найден: {pdf_path}")
