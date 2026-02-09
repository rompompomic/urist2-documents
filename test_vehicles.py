# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from processor import DocumentProcessor

# Тестовые данные ГИБДД (как после парсинга)
test_data = [
    {
        "Есть_транспорт": True,
        "Транспортные_средства": [
            {
                "Марка_модель": "Lada Granta",
                "VIN": "XTAGFK330JY123456",
                "Год_выпуска": "2020",
                "Гос_номер": "А123БВ777",
                "Тип_ТС": "Легковой",
                "Стоимость": "500000",
            }
        ]
    }
]

print('\n=== ВХОДНЫЕ ДАННЫЕ ===')
print(f'Тип данных: {type(test_data)}')
print(f'Количество документов: {len(test_data)}')
print(f'Первый документ: {test_data[0]}')
print(f'Ключи первого документа: {list(test_data[0].keys())}')
print(f'Тип Транспортные_средства: {type(test_data[0].get("Транспортные_средства"))}')
if test_data[0].get("Транспортные_средства"):
    print(f'Первое ТС: {test_data[0]["Транспортные_средства"][0]}')

# Проверяем что вернет format_vehicles_table
result = DocumentProcessor.format_vehicles_table(test_data)

print('\n=== РЕЗУЛЬТАТ format_vehicles_table ===')
for key, value in result.items():
    print(f'{key}: {value}')

print('\n=== ПРОВЕРКА: был ли найден автомобиль? ===')
if result["автомобили"]:
    print('✅ Автомобиль найден!')
    print(f'Данные: {result["автомобили"]}')
else:
    print('❌ Автомобиль НЕ найден!')
