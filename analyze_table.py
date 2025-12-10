"""Анализ структуры таблицы"""
from docx import Document
from pathlib import Path

doc_path = Path("test_separate_rows.docx")
doc = Document(doc_path)

print("=== ТАБЛИЦЫ В ДОКУМЕНТЕ ===")
for idx, table in enumerate(doc.tables):
    print(f"\nТаблица {idx}:")
    print(f"  Строк: {len(table.rows)}")
    print(f"  Столбцов: {len(table.columns)}")
    
    if len(table.rows) > 0:
        print(f"\n  Заголовки (строка 0):")
        for col_idx, cell in enumerate(table.rows[0].cells):
            print(f"    Столбец {col_idx}: '{cell.text[:50]}'")
        
        if len(table.rows) > 1:
            print(f"\n  Первая строка данных (строка 1):")
            for col_idx, cell in enumerate(table.rows[1].cells):
                print(f"    Столбец {col_idx}: '{cell.text[:50]}'")
