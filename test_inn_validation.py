"""Тест валидации ИНН"""

def validate_inn(inn: str) -> bool:
    """Проверяет корректность ИНН по контрольной сумме."""
    if not inn or not inn.isdigit():
        return False
        
    if len(inn) == 10:
        # ИНН юридического лица (10 цифр)
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(int(inn[i]) * coefficients[i] for i in range(9)) % 11
        checksum = checksum % 10
        return checksum == int(inn[9])
        
    elif len(inn) == 12:
        # ИНН физического лица (12 цифр)
        # Первая контрольная цифра
        coefficients1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum1 = sum(int(inn[i]) * coefficients1[i] for i in range(10)) % 11
        checksum1 = checksum1 % 10
        
        # Вторая контрольная цифра  
        coefficients2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum2 = sum(int(inn[i]) * coefficients2[i] for i in range(11)) % 11
        checksum2 = checksum2 % 10
        
        return checksum1 == int(inn[10]) and checksum2 == int(inn[11])
    
    return False


# Тестирование ИНН из лога
test_inns = {
    # ИНН, который пользователь называет неправильным
    "9548295777": None,  # Должен быть невалидным
    
    # Известные валидные ИНН из лога
    "7710140679": "АО «ТБанк»",  # Т-Банк
    "7707083893": "ПАО «Сбербанк»",  # Сбербанк
    "7728168971": "АО «Альфа-Банк»",  # Альфа-Банк
    "7702070139": "ПАО «ВТБ»",  # ВТБ
    "2340344446": "ООО МКК «СМСФИНАНС»",  # Другой ИНН для СМСФинанс
    "7300032408": "ООО МКК «Эквазайм»",  # Эквазайм
}

print("=" * 80)
print("ТЕСТ ВАЛИДАЦИИ ИНН")
print("=" * 80)

for inn, company in test_inns.items():
    is_valid = validate_inn(inn)
    status = "✅ ВАЛИДЕН" if is_valid else "❌ НЕВАЛИДЕН"
    company_info = f" ({company})" if company else " (подозрительный из логов)"
    print(f"{status}  {inn}{company_info}")

print("\n" + "=" * 80)
print("ВЫВОД:")
print("=" * 80)
print("ИНН 9548295777 - НЕВАЛИДЕН (контрольная сумма не сходится)")
print("Этот ИНН нужно игнорировать и искать правильный в RusProfile")
