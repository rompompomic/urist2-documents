import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the processor
try:
    from processor import DocumentProcessor
except ImportError:
    print("Error: Could not import DocumentProcessor from processor.py")
    exit(1)

def run_test():
    # Configuration
    pdf_path = Path("Отчет_НБКИ (6).pdf")
    
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} not found!")
        return

    print(f"Starting test scan for NBKI report: {pdf_path}")
    print("-" * 50)
    
    # Initialize processor
    try:
        processor = DocumentProcessor()
        print("Processor initialized successfully.")
    except Exception as e:
        print(f"Error initializing processor: {e}")
        return

    # Run processing
    start_time = time.time()
    try:
        # debtor_fio is optional, leaving it empty for this test
        result = processor.process_pdf(pdf_path)
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return
    end_time = time.time()
    
    duration = end_time - start_time
    print("-" * 50)
    print(f"Processing completed in {duration:.2f} seconds")
    print(f"Document Type: {result.document_type}")
    print(f"Pages: {result.pages}")
    
    if result.error:
        print(f"Error returned: {result.error}")
    elif result.pages == 0 and not result.data:
        print("Success: NBKI processing was skipped as expected.")
    else:
        # Save full result to JSON
        output_file = "nbki_scan_result.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.data, f, ensure_ascii=False, indent=2)
        print(f"Full JSON result saved to: {output_file}")
        
        # Display Credit Summary
        data = result.data
        credits = data.get("Кредиты", [])
        
        print(f"\nExtracted {len(credits)} credits:")
        
        total_debt = 0.0
        for i, credit in enumerate(credits, 1):
            creditor = credit.get("Кредитор", "Не указан")
            
            # Format amount
            amount_raw = credit.get("Сумма", 0)
            amount = 0.0
            try:
                if isinstance(amount_raw, (int, float)):
                    amount = float(amount_raw)
                elif isinstance(amount_raw, str):
                    clean_str = amount_raw.replace(" ", "").replace(",", ".")
                    amount = float(clean_str)
            except:
                pass
                
            total_debt += amount
            
            # Get opened date
            date_open = credit.get("Дата_открытия", "н/д")
            
            print(f"{i}. {creditor} | Дата: {date_open} | Сумма: {amount:,.2f}")
            
        print("-" * 30)
        print(f"Total Debt: {total_debt:,.2f}")
        
        # Check specific fields that were problematic
        print("\nHeader Info:")
        print(f"FIO: {data.get('ФИО')}")
        print(f"Date of Report: {data.get('Дата_отчета')}")

if __name__ == "__main__":
    run_test()
