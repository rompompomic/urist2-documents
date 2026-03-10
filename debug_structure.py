
import sys
import os
import pdfplumber
from pathlib import Path

def extract_structured_text(pdf_path: Path) -> str:
    """Extracts text preserving table layouts using pdfplumber."""
    
    output_lines = []
    
    print(f"Opening PDF: {pdf_path.name}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Processing {total_pages} pages...")
            
            for i, page in enumerate(pdf.pages):
                # 1. Сначала пробуем извлечь таблицы
                tables = page.extract_tables()
                
                # 2. Извлекаем обычный текст, пытаясь сохранить layout
                text = page.extract_text(layout=True)
                
                output_lines.append(f"\n{'='*30} PAGE {i+1} {'='*30}\n")
                
                if text:
                    output_lines.append(text)
                else:
                    output_lines.append("[NO TEXT EXTRACTED]")
                
                if tables:
                    output_lines.append(f"\n--- DETECTED {len(tables)} TABLES ON PAGE {i+1} ---\n")
                    for t_idx, table in enumerate(tables):
                        output_lines.append(f"Table {t_idx+1}:")
                        for row in table:
                            # Очищаем None значения и форматируем строку
                            clean_row = [str(cell).replace('\n', ' ') if cell is not None else "" for cell in row]
                            output_lines.append(" | ".join(clean_row))
                        output_lines.append("-" * 20)
                
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return ""
        
    return "\n".join(output_lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_structure.py <path_to_pdf>")
        print("Using default: Кредитный_отчет_НБКИ.pdf")
        pdf_path = Path("Кредитный_отчет_НБКИ.pdf")
    else:
        pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Error: File {pdf_path} not found")
        return

    # Extract Structured Text
    structured_text = extract_structured_text(pdf_path)
    
    if not structured_text:
        print("Failed to extract structured text.")
        return

    # Save to file
    output_filename = f"debug_structured_{pdf_path.stem}.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(structured_text)
            
    print(f"\nSuccess! Structured text saved to: {output_filename}")
    print("Open this file to see text with layout preservation.")

if __name__ == "__main__":
    main()
