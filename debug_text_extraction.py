import os
import sys
import json
import time
import pymupdf  # Replacing pypdfium2 with pymupdf (fitz) for better layout preservation
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import DocumentProcessor to get prompts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from processor import DocumentProcessor
except ImportError:
    print("Error importing DocumentProcessor. Make sure processor.py is in the same directory.")
    sys.exit(1)

def extract_text_from_pdf(pdf_path):
    """Extracts text from PDF using PyMuPDF (fitz) preserving physical layout."""
    text_content = []
    
    try:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        print(f"Document has {total_pages} pages.")
        
        for i in range(total_pages):
            page = doc[i]
            # Use "text" by default, try layout only if needed
            # The previous crash "Error extracting text: " with empty exception possibly due to "layout" key
            # or version issues.
            try:
                # Let's try "blocks" or simpler "text" first to verify basic functionality
                # Then we can iterate over blocks to reconstruct layout if needed
                text = page.get_text("text") 
            except Exception as e_page:
                print(f"Page {i+1} error: {e_page}")
                text = ""
                
            text_content.append(f"--- Page {i+1} ---\n{text}")
            
        return "\n".join(text_content)
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def process_text_with_gpt(text, prompt_instruction):
    """Sends extracted text to GPT-4o."""
    try:
        if not text.strip():
            return "Error: No text extracted from PDF."
            
        print(f"Sending {len(text)} characters of text to GPT-4o...")
        
        # Use valid JSON instruction
        full_system_prompt = prompt_instruction + "\n\nВАЖНО: Верни ТОЛЬКО валидный JSON. Не добавляй markdown разметку. Просто текст JSON."

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": f"Вот часть кредитного отчета. Извлеки данные:\n\n{text}"}
            ],
            temperature=0.1,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"GPT Error: {e}")
        return "{}"

def main():
    # Configuration - LIST of files to process
    filenames = ["отчет_окб.pdf", "отчет_скоринг_бюро.pdf"] 
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Store results for all files
    data_map = {}

    for filename in filenames:
        file_path = os.path.join(script_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        print(f"\n{'='*50}")
        print(f"Processing {filename}...")
        print(f"{'='*50}")
        
        # 1. Detect document type and get prompt
        doc_type, prompt = DocumentProcessor.detect_document_type(filename)
        # Fallback logic
        if doc_type == "общий": 
             if "окб" in filename.lower(): doc_type = "отчет_окб"
             elif "бюро" in filename.lower() or "бки" in filename.lower(): doc_type = "отчет_бки"
             elif "нбки" in filename.lower(): doc_type = "отчет_нбки"
             
             if doc_type in DocumentProcessor.DOCUMENT_TYPES:
                 prompt = DocumentProcessor.DOCUMENT_TYPES[doc_type]["prompt"]
             
        print(f"Detected type: {doc_type}")
        
        # 2. Extract Text
        print("Extracting text pages...")
        full_text = extract_text_from_pdf(file_path)
        pages = full_text.split("--- Page ")
        pages = [p for p in pages if p.strip()]
        
        total_pages = len(pages)
        print(f"Total pages extracted: {total_pages}")

        # 3. Process in Batches
        BATCH_SIZE = 40
        file_credits = []
        
        print(f"Processing in batches of {BATCH_SIZE} pages...")
        
        for i in range(0, total_pages, BATCH_SIZE):
            batch_pages = pages[i : i + BATCH_SIZE]
            batch_text = "\n--- Page ".join(batch_pages) 
            
            print(f"   Batch {i // BATCH_SIZE + 1}: Pages {i+1} to {min(i+BATCH_SIZE, total_pages)}")
            
            result = process_text_with_gpt(batch_text, prompt)
            
            try:
                if result.startswith("```json"): result = result[7:]
                if result.endswith("```"): result = result[:-3]
                
                data = json.loads(result)
                extracted_list = data.get("Кредиты") or data.get("contracts") or data.get("credits") or []
                
                if extracted_list:
                    print(f"      Found {len(extracted_list)} credits in this batch.")
                    file_credits.extend(extracted_list)
                else:
                    print(f"      No credits found in this batch.")
                    
            except Exception as e:
                print(f"      Error parsing batch: {e}")
        
        # Add to global data map
        if doc_type not in data_map:
            data_map[doc_type] = []
        data_map[doc_type].append({"Кредиты": file_credits})

    # 4. Deduplication & Merging (Global)
    print("\n" + "="*50)
    print("GLOBAL DEDUPLICATION & MERGING")
    print("="*50)
    
    merged_credits = DocumentProcessor.merge_credit_reports(data_map)
    
    print("\n--- Final Merged Credit List ---")
    total_debt = 0.0
    for idx, credit in enumerate(merged_credits, 1):
        creditor = credit.get('Кредитор', 'Unknown')
        
        amount = credit.get('Сумма_задолженности') or credit.get('Текущая_задолженность') or credit.get('Сумма', 0)
        try:
             amount_float = float(amount)
        except:
             amount_float = 0.0
             
        total_debt += amount_float
        
        date = credit.get('Дата_договора') or credit.get('Дата_сделки', 'xx.xx.xxxx')
        print(f"  {idx}. {creditor} | {amount} | {date}")

    print(f"\nTotal Current Debt: {total_debt:,.2f}")

if __name__ == "__main__":
    main()
