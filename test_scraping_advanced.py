import sys
import os
import time

# Добавляем текущую директорию в путь
sys.path.append(os.getcwd())

from processor import DocumentProcessor

def test_rusprofile_scraping_advanced():
    test_companies = [
        "ООО МКК «Стратосфера»",
    ]

    print("=== ЗАПУСК РАСШИРЕННОГО ТЕСТА СКРАПИНГА RUSPROFILE ===")
    print("Проверка механизмов маскировки (User-Agent + Задержки + Cookies)")
    print("-" * 60)

    for i, company in enumerate(test_companies):
        print(f"\n[{i+1}/{len(test_companies)}] 🔍 Поиск компании: '{company}'")
        
        start_time = time.time()
        try:
            # Вызываем метод поиска
            inn, address = DocumentProcessor.parse_inn_and_address_from_rusprofile(company)
            
            elapsed = time.time() - start_time
            
            if inn:
                print(f"✅ УСПЕХ! (за {elapsed:.2f} сек)")
                print(f"   ИНН: {inn}")
                print(f"   Адрес: {address}")
            else:
                print(f"❌ НЕ НАЙДЕНО (за {elapsed:.2f} сек)")
                
        except Exception as e:
            print(f"💥 ОШИБКА: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "-" * 60)
    print("=== ТЕСТ ЗАВЕРШЕН ===")

if __name__ == "__main__":
    test_rusprofile_scraping_advanced()