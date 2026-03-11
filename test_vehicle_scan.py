
import os
import sys
import json
from pathlib import Path
from processor import DocumentProcessor

# Setup output directory
output_dir = Path("outputs_test_vehicle")
output_dir.mkdir(exist_ok=True)

# Files to test
files_to_test = [
    "ПТС.pdf",
    "СТС.pdf"
]

processor = DocumentProcessor()

print(f"--- Starting Vehicle Scan Test ---")

for filename in files_to_test:
    file_path = Path(filename)
    if not file_path.exists():
        print(f"File not found: {filename}")
        continue
        
    print(f"\nProcessing: {filename}")
    try:
        # Using process_pdf directly
        result = processor.process_pdf(file_path)
        
        print(f"Document Type: {result.document_type}")
        print(f"Extracted Data:")
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n--- End of Test ---")
