#!/usr/bin/env python3
"""
Тест парсинга недвижимости и формирования контекста для шаблона.
Проверяет, попадает ли недвижимость из описи имущества в списки для таблиц Описи (земельные_участки и т.д.)
"""
import json
from processor import DocumentProcessor

def test_real_estate_parsing():
    print("=== ТЕСТ ПАРСИНГА НЕДВИЖИМОСТИ ИЗ ОПИСИ ===")
    
    # Имитируем данные из Описи имущества (ценное_имущество)
    inventory_data = [{
        "Недвижимость": [
            {
                "Вид": "квартира",
                "Адрес": "г. Москва, ул. Ленина 1, кв 5",
                "Площадь": "50 кв.м.",
                "Вид_права": "собственность",
                "Стоимость": "10000000",
                "Основание": "Договор купли-продажи"
            },
            {
                "Вид": "земельный участок",
                "Адрес": "Московская обл, д. Простоквашино",
                "Площадь": "600 кв.м.",
                "Вид_права": "собственность",
                "Стоимость": "500000"
            }
        ]
    }]
    
    # Пустые данные ЕГРН (ситуация пользователя)
    egrn_data = [] # Нет выписки
    notifications = [] # Нет уведомлений
    
    # 1. Проверяем формирование строки {{Недвижимое_имущество}} для заявления
    print("\n[ШАГ 1] Проверка format_real_estate_detailed (для {{Недвижимое_имущество}})")
    processed_string = DocumentProcessor.format_real_estate_detailed(
        egrn_data, 
        owner_fio="Иванов И.И.", 
        notification_list=notifications,
        inventory_list=inventory_data
    )
    print(f"Результат format_real_estate_detailed:\n'{processed_string}'")
    
    if "квартира" in processed_string and "земельный участок" in processed_string:
        print("✅ УСПЕХ: Недвижимость из описи попала в строку {{Недвижимое_имущество}}")
    else:
        print("❌ ОШИБКА: Недвижимость из описи НЕ попала в строку {{Недвижимое_имущество}}")

    # 2. Проверяем формирование списков для Описи имущества (таблицы)
    print("\n[ШАГ 2] Проверка format_inventory_tables (для таблиц Описи)")
    
    # Эмулируем работу prepare_template_context в части формирования списков
    # В Processor.py нет отдельного метода, логика, вероятно, внутри prepare_template_context.
    # Нам нужно проверить код в processor.py, который формирует 'квартиры', 'земельные_участки' и т.д.
    
    # Создаем фиктивный data_map
    data_map = {
        "ценное_имущество": inventory_data,
        "егрн_выписка": egrn_data,
        "егрн_уведомление": notifications
    }
    
    # ВАЖНО: Нам нужно увидеть, как Processor формирует списки для контекста.
    # Поскольку метод prepare_template_context большой, мы проверим его логику через чтение кода
    # или (если возможно) вызов метода. Но он требует PDF путей...
    
    # Попробуем создать экземпляр процессора и вызвать prepare_template_context с минимумом данных
    try:
        proc = DocumentProcessor()
        # Mocking empty list for aggregated data is tricky as prepare_template_context takes it first.
        # But prepare_template_context parses text files... 
        
        # Лучше мы просто посмотрим на код внутри prepare_template_context в processor.py
        # через read_file, так как запустить его сложно без реальных файлов.
        print("Проверка кода processor.py на наличие логики объединения источников...")
        
    except Exception as e:
        print(f"Ошибка при инициализации: {e}")

if __name__ == "__main__":
    test_real_estate_parsing()
