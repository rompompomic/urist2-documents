
import sys
import re
import fitz  # PyMuPDF
from pathlib import Path

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts text from PDF using PyMuPDF (fitz) preserving physical layout."""
    text_content = []
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"Opening PDF: {pdf_path.name} ({total_pages} pages)")
        
        for i in range(total_pages):
            page = doc[i]
            try:
                # Use simple text extraction which is robust and sufficient for GPT-5.1
                text = page.get_text("text") 
            except Exception as e:
                print(f"      [TEXT] Error extracting page {i+1}: {e}")
                text = ""
            text_content.append(f"--- Page {i+1} ---\n{text}")
        return "\n".join(text_content)
    except Exception as e:
        print(f"      [TEXT] Error extracting text: {e}")
        return ""

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_credit_report.py <path_to_pdf>")
        print("Using default: Кредитный_отчет_НБКИ.pdf")
        pdf_path = Path("Кредитный_отчет_НБКИ.pdf")
    else:
        pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Error: File {pdf_path} not found")
        return

    # 1. Extract Text
    full_text = extract_text_from_pdf(pdf_path)
    
    # 2. Split into chunks logic (simulating processor.py)
    # Re-split by the marker we added
    # Using regex to split by --- Page X --- markers
    pages = re.split(r'--- Page \d+ ---\n', full_text)
    # Remove empty first element if any
    pages = [p for p in pages if p.strip()]
    
    total_pages = len(pages)
    print(f"Extracted {total_pages} pages of text")

    # Chunk config
    CHUNK_SIZE = 40  # Pages per chunk
    chunks = []
    current_chunk = []
    
    for i, p in enumerate(pages):
        # Add page marker back for clarity
        page_content = f"--- Page {i+1} ---\n{p}"
        current_chunk.append(page_content)
        if len(current_chunk) >= CHUNK_SIZE:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
    
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    print(f"Split into {len(chunks)} chunks for GPT processing")

    # 3. Save to file
    output_filename = f"debug_text_{pdf_path.stem}.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(f"=== CHUNK {i+1}/{len(chunks)} ===\n")
            f.write(chunk)
            f.write("\n\n" + "="*50 + "\n\n")
            
    print(f"\nSuccess! Extracted text saved to: {output_filename}")
    print("You can now open this file to see exactly what text is sent to ChatGPT.")

if __name__ == "__main__":
    main()
