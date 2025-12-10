"""Детальный анализ таблицы кредиторов"""
from docx import Document
from pathlib import Path

doc_path = Path("test_separate_rows.docx")
doc = Document(doc_path)

table = doc.tables[1]  # Таблица кредиторов

print("=== ТАБЛИЦА КРЕДИТОРОВ (детально) ===\n")
print(f"Всего строк: {len(table.rows)}")
print(f"Всего столбцов: {len(table.columns)}\n")

for row_idx, row in enumerate(table.rows[:8]):  # Первые 8 строк
    print(f"Строка {row_idx}:")
    for col_idx, cell in enumerate(row.cells):
        text = cell.text.strip().replace('\n', ' ')[:40]
        print(f"  [{col_idx}] = '{text}'")
    print()
