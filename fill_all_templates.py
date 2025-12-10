"""Заполнение всех шаблонов документов."""
import json
from pathlib import Path
from processor import DocumentProcessor, OUTPUT_DIR

print("=" * 80)
print("  ЗАПОЛНЕНИЕ ВСЕХ ШАБЛОНОВ ДОКУМЕНТОВ")
print("=" * 80)
print()

# Создаем папку для результатов
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Загружаем результаты обработки
result_file = Path("docs/результат_обработки.json")
with open(result_file, encoding='utf-8') as f:
    data = json.load(f)

# Собираем данные по типам
data_map = {}
for doc in data:
    doc_type = doc['document_type']
    if doc_type not in data_map:
        data_map[doc_type] = []
    data_map[doc_type].append(doc['data'])

print(f"OK - Загружено {len(data)} документов")
print(f"OK - Типов документов: {len(data_map)}")
print()

# Формируем контекст для шаблона
print("Формирование контекста шаблона...")
context = DocumentProcessor.prepare_template_context(data_map)
print("OK - Контекст сформирован")
print()

# Список шаблонов для заполнения
templates = [
    {
        "name": "Заявление о банкротстве",
        "template": "templ/Заявление на банкротство.docx",
        "output": OUTPUT_DIR / "Заявление на банкротство (заполненное).docx",
        "dynamic": True  # Используем DocxTemplate для корректной замены переменных
    },
    {
        "name": "Ходатайство об отсрочке",
        "template": "templ/Ходатайство об отсрочке.docx",
        "output": OUTPUT_DIR / "Ходатайство об отсрочке (заполненное).docx",
        "dynamic": True  # Используем DocxTemplate для корректной замены переменных
    },
    {
        "name": "Ходатайство о реализации имущества",
        "template": "templ/Ходатайство о реализации имущества.docx",
        "output": OUTPUT_DIR / "Ходатайство о реализации имущества (заполненное).docx",
        "dynamic": True  # Используем DocxTemplate для корректной замены переменных
    },
    {
        "name": "Список кредиторов и должников",
        "template": "templ/Список кредиторов и должников.docx",
        "output": OUTPUT_DIR / "Список кредиторов и должников (заполненное).docx",
        "dynamic": True  # ДИНАМИЧЕСКИЙ ШАБЛОН с таблицами
    },
    {
        "name": "Опись имущества",
        "template": "templ/Опись имущества.docx",
        "output": OUTPUT_DIR / "Опись имущества (заполненное).docx",
        "dynamic": True  # ДИНАМИЧЕСКИЙ ШАБЛОН с таблицами
    },
]

# Заполняем каждый шаблон
results = []
for item in templates:
    template_path = Path(item["template"])
    output_path = Path(item["output"])
    is_dynamic = item.get("dynamic", False)
    
    print(f"> {item['name']}:")
    
    if not template_path.exists():
        print(f"   ERROR - Шаблон не найден: {template_path}")
        results.append({"name": item["name"], "status": "ERROR - Шаблон не найден"})
        continue
    
    try:
        # Выбираем функцию в зависимости от типа шаблона
        if is_dynamic:
            # Динамический шаблон с Jinja2 (для таблиц)
            DocumentProcessor.fill_docx_template_dynamic(template_path, output_path, context)
        else:
            # Простой шаблон (замена переменных)
            DocumentProcessor.fill_docx_template(template_path, output_path, context)
        
        print(f"   OK - Сохранено в {output_path}")
        results.append({"name": item["name"], "status": "OK", "path": output_path})
    except PermissionError:
        print(f"   WARNING - Файл открыт в Word: {output_path.name}")
        results.append({"name": item["name"], "status": "WARNING - Файл открыт"})
    except Exception as e:
        print(f"   ERROR - {e}")
        results.append({"name": item["name"], "status": f"ERROR - {e}"})
    
    print()

# Итоговая сводка
print("=" * 80)
print("  ИТОГОВАЯ СВОДКА")
print("=" * 80)
print()

success_count = sum(1 for r in results if r["status"] == "OK")
total_count = len(results)

for result in results:
    print(f"{result['status']:<30} {result['name']}")

print()
print(f"Успешно заполнено: {success_count} из {total_count}")
print(f"Все файлы сохранены в: {OUTPUT_DIR.absolute()}")
print()

if success_count == total_count:
    print("SUCCESS! ВСЕ ДОКУМЕНТЫ УСПЕШНО ЗАПОЛНЕНЫ!")
elif success_count > 0:
    print("WARNING - Некоторые документы не были заполнены. Проверьте сообщения выше.")
else:
    print("ERROR - Ни один документ не был заполнен. Проверьте ошибки выше.")

print()
print("=" * 80)
