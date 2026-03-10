
import sys
import os
import json
import time
from pathlib import Path
from processor import DocumentProcessor

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_credit_scan.py <path_to_pdf>")
        print("Using default: Кредитный_отчет_НБКИ.pdf")
        pdf_path = Path("Кредитный_отчет_НБКИ.pdf")
    else:
        pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Error: File {pdf_path} not found")
        return

    print(f"\n{'='*50}")
    print(f"TESTING CREDIT REPORT SCAN: {pdf_path.name}")
    print(f"{'='*50}\n")

    processor = DocumentProcessor()
    
    # Manually detect type to simulate behavior (though process_pdf does it too)
    doc_type, base_prompt = processor.detect_document_type(pdf_path.name)
    print(f"Detected Document Type: {doc_type}")
    
    if doc_type not in ["отчет_окб", "отчет_бки", "отчет_нбки"]:
        print(f"WARNING: Detected type '{doc_type}' is usually not processed as a credit report in this test context.")
        print("Continuing anyway to test process_pdf...")

    start_time = time.time()
    
    # Call the main processing method
    # This will trigger:
    # 1. extract_text_from_pdf (now using pdfplumber)
    # 2. process_pdf_with_text_extraction (chunking + GPT calls)
    try:
        result = processor.process_pdf(pdf_path)
    except Exception as e:
        print(f"CRITICAL ERROR during processing: {e}")
        import traceback
        traceback.print_exc()
        return

    elapsed = time.time() - start_time
    
    print(f"\n{'='*50}")
    print(f"PROCESSING COMPLETED in {elapsed:.1f}s")
    print(f"{'='*50}\n")
    
    if result.error:
        print(f"RESULT ERROR: {result.error}")
    else:
        print("RESULT SUCCESS!")
        print(f"Credits Found: {len(result.data.get('Кредиты', [])) if isinstance(result.data, dict) else 'N/A'}")
        
        # Save result to file for inspection
        output_file = f"result_{pdf_path.stem}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.data, f, ensure_ascii=False, indent=2)
            
        print(f"\nFull JSON result saved to: {output_file}")
        
        # Print a summary of found credits
        if isinstance(result.data, dict) and "Кредиты" in result.data:
            print("\n--- CREDITS SUMMARY ---")
            for i, credit in enumerate(result.data["Кредиты"]):
                print(f"{i+1}. {credit.get('Кредитор', 'Unknown')} | {credit.get('Сумма', '0')} | {credit.get('Дата_договора', 'N/A')}")

if __name__ == "__main__":
    main()
