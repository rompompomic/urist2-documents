"""Тестовый файл для проверки нормализации названий кредиторов через GPT"""

from processor import DocumentProcessor

# Тестовые названия кредиторов с опечатками и разными форматами
test_creditors = [
    "Общество С Ограниченной Ответственностью МКК Денежная Крепость",
    "ООО МКК Эквазаим",
    "ооо мкк эквазаим",
    "ПАО СБЕРБАНК",
    "пао сбербанк россии",
    "АО АЛЬФА-БАНК",
    "Ао Альфа Банк",
    "МТС-БАНК ПАО",
    "ПАО ВТБ",
    "втб банк",
    "Тинькофф Банк АО",
    "АО Т-Банк",
    "ООО МФК Займер",
    "ЗАЙМЕР",
    "Общество с ограниченной ответственностью микрокредитная компания турбозайм",
]

print("=" * 80)
print("ТЕСТ НОРМАЛИЗАЦИИ НАЗВАНИЙ КРЕДИТОРОВ ЧЕРЕЗ GPT")
print("=" * 80)
print()

print("Исходные названия:")
for i, name in enumerate(test_creditors, 1):
    print(f"{i}. {name}")

print()
print("-" * 80)
print("Запуск нормализации через GPT...")
print("-" * 80)
print()

# Вызываем функцию нормализации
normalized = DocumentProcessor.normalize_creditor_names_with_gpt(test_creditors)

print()
print("=" * 80)
print("РЕЗУЛЬТАТЫ НОРМАЛИЗАЦИИ")
print("=" * 80)
print()

if normalized:
    for original, corrected in normalized.items():
        print(f"✓ {original}")
        print(f"  → {corrected}")
        print()
    
    print("=" * 80)
    print(f"Успешно нормализовано: {len(normalized)} из {len(test_creditors)}")
    print("=" * 80)
else:
    print("❌ Нормализация не удалась")
