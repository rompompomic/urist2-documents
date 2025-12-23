import json
from pathlib import Path
from decimal import Decimal

p = Path('outputs/4d9ab0fc-33d4-46d9-8a7f-1023cb11ca87/result.json')
with open(p, encoding='utf-8') as f:
    d = json.load(f)

credits = d.get('credits', [])
print(f'Всего кредиторов: {len(credits)}')
print(f'\nОбщая сумма долга: {d.get("Общая_сумма_долга", "не указано")}\n')

total = 0
print('Список кредитов:')
print('-' * 80)

for i, c in enumerate(credits, 1):
    kreditor = c.get('Кредитор', '?')
    data = c.get('Дата_договора', '?')
    inn = c.get('ИНН_кредитора', 'нет')
    dolg = c.get('Задолженность_в_том_числе', '0')
    
    print(f'{i}. {kreditor}')
    print(f'   Дата: {data} | ИНН: {inn}')
    print(f'   Долг: {dolg}')
    
    # Считаем
    try:
        dolg_float = float(str(dolg).replace(' ', '').replace(',', '.'))
        total += dolg_float
    except:
        pass

print('-' * 80)
print(f'\n💰 ИТОГО по кредитам: {total:,.2f} руб.')
print(f'📊 Ожидается: 529 525.98 руб.')

# Проверяем налоги
taxes = d.get('taxes', [])
total_tax = 0
if taxes:
    print(f'\n💸 Налоги:')
    print('-' * 80)
    for i, t in enumerate(taxes, 1):
        name = t.get('Налог_сбор_или_иной_обяз_платеж', '?')
        amount = t.get('Сумма_обяз_платежа', '0')
        print(f'{i}. {name}: {amount}')
        try:
            amount_float = float(str(amount).replace(' ', '').replace(',', '.'))
            total_tax += amount_float
        except:
            pass
    print('-' * 80)
    print(f'💸 ИТОГО налогов: {total_tax:,.2f} руб.')

grand_total = total + total_tax
print(f'\n🎯 ОБЩАЯ СУММА (кредиты + налоги): {grand_total:,.2f} руб.')
print(f'❓ Разница с ожидаемой: {abs(grand_total - 529525.98):,.2f} руб.')
