"""
Тестовый скрипт для проверки парсинга RusProfile
"""
from processor import DocumentProcessor

# Тестовые компании
test_companies = [
    "ООО МКК «Эквазайм»",  # Должна открыться сразу страница
    "Сбербанк",             # Может показать список
    "ООО «Компания»",       # Обычный случай
]

print("=" * 80)
print("ТЕСТ ПАРСИНГА RUSPROFILE")
print("=" * 80)

for company in test_companies:
    print(f"\n{'=' * 80}")
    print(f"Компания: {company}")
    print("=" * 80)
    
    inn, address = DocumentProcessor.parse_inn_and_address_from_rusprofile(company)
    
    print(f"\n✓ Результат:")
    print(f"  ИНН: {inn if inn else 'НЕ НАЙДЕН'}")
    print(f"  Адрес: {address if address else 'НЕ НАЙДЕН'}")
    print()

print("=" * 80)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 80)
