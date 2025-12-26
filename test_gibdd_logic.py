"""Тестовый файл для проверки логики определения справки ГИБДД"""

from processor import DocumentProcessor

# СЦЕНАРИЙ 1: Только ПТС (без справки ГИБДД) - текст должен подставиться
print("=" * 80)
print("СЦЕНАРИЙ 1: Только ПТС/СТС (без справки)")
print("=" * 80)
docs_scenario_1 = [
    {
        "Является_справкой_ГИБДД": False,
        "Тип_ТС": "легковой",
        "Марка_модель": "ВАЗ 11183 Lada Kalina",
        "VIN": "XTA11183080124632",
        "Гос_номер": "M946MO174",
        "Год_выпуска": "2007",
        "Документ": {
            "Тип": "СТС",
            "Дата_регистрации": "04.07.2024"
        }
    }
]

result_1 = DocumentProcessor.format_vehicles_table(docs_scenario_1)
print(f"Автомобилей: {len(result_1['автомобили'])}")
print(f"Текст Нету_гибдд: '{result_1['Нету_гибдд']}'")
print(f"Ожидается: текст ДОЛЖЕН подставиться")
print(f"Результат: {'✓ PASS' if result_1['Нету_гибдд'] else '✗ FAIL'}")
print()

# СЦЕНАРИЙ 2: Справка ГИБДД об отсутствии - текст НЕ должен подставиться
print("=" * 80)
print("СЦЕНАРИЙ 2: Справка ГИБДД об отсутствии транспорта")
print("=" * 80)
docs_scenario_2 = [
    {
        "Результат": "транспорт отсутствует",
        "Является_справкой_ГИБДД": True,
        "Документ": {
            "Тип": "справка об отсутствии"
        }
    }
]

result_2 = DocumentProcessor.format_vehicles_table(docs_scenario_2)
print(f"Автомобилей: {len(result_2['автомобили'])}")
print(f"Текст Нету_гибдд: '{result_2['Нету_гибдд']}'")
print(f"Ожидается: текст НЕ должен подставиться")
print(f"Результат: {'✓ PASS' if not result_2['Нету_гибдд'] else '✗ FAIL'}")
print()

# СЦЕНАРИЙ 3: Нет документов ГИБДД вообще - текст должен подставиться
print("=" * 80)
print("СЦЕНАРИЙ 3: Нет документов ГИБДД вообще")
print("=" * 80)
docs_scenario_3 = []

result_3 = DocumentProcessor.format_vehicles_table(docs_scenario_3)
print(f"Автомобилей: {len(result_3['автомобили'])}")
print(f"Текст Нету_гибдд: '{result_3['Нету_гибдд']}'")
print(f"Ожидается: текст ДОЛЖЕН подставиться")
print(f"Результат: {'✓ PASS' if result_3['Нету_гибдд'] else '✗ FAIL'}")
print()

# ИТОГИ
print("=" * 80)
print("ИТОГИ ТЕСТИРОВАНИЯ")
print("=" * 80)
pass_count = sum([
    bool(result_1['Нету_гибдд']),
    not bool(result_2['Нету_гибдд']),
    bool(result_3['Нету_гибдд'])
])
print(f"Пройдено тестов: {pass_count}/3")
if pass_count == 3:
    print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
else:
    print("✗ ЕСТЬ ОШИБКИ")
