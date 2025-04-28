# import json
# import pdfplumber
# import io
# from pypdf import PdfReader
# import os

# def extract_raw_json(file_stream: io.BytesIO) -> dict:
#     """Extract all text from a PDF into raw JSON."""
#     try:
#         reader = PdfReader(file_stream)
#         text = "".join(page.extract_text() or "" for page in reader.pages)
#         return {"raw_text": text}
#     except Exception as e:
#         return {"error": str(e)}

# def pdf_to_json(pdf_path: str, json_path: str, use_raw: bool = False) -> None:
#     """Convert PDF to JSON, either using pdfplumber (structured) or PyPDF2 (raw)."""
#     data = {}
    
#     if use_raw:
#         # Use raw text extraction
#         with open(pdf_path, 'rb') as file:
#             file_stream = io.BytesIO(file.read())
#             data = extract_raw_json(file_stream)
#     else:
#         # Use structured text extraction with pdfplumber
#         data = {"pages": []}
#         with pdfplumber.open(pdf_path) as pdf:
#             for page_num, page in enumerate(pdf.pages, start=1):
#                 text = page.extract_text()
#                 page_data = {
#                     "page_number": page_num,
#                     "content": text if text else ""
#                 }
#                 data["pages"].append(page_data)
    
#     # Save extracted data to JSON file
#     with open(json_path, 'w', encoding='utf-8') as json_file:
#         json.dump(data, json_file, indent=4, ensure_ascii=False)

# def main():
#     # File paths
#     pdf_file = "airtable_attachments/attachments/Order_rec2lvVfoMugIXz9g.pdf"
#     json_file = "output_Order.json"
    
#     # Check if PDF file exists
#     if not os.path.exists(pdf_file):
#         print(f"Error: PDF file '{pdf_file}' not found.")
#         return
    
#     # Convert PDF to JSON (use_raw=True for raw text, False for structured)
#     pdf_to_json(pdf_file, json_file, use_raw=False)
#     print(f"JSON created: {json_file}")

# if __name__ == "__main__":
#     main()

import json
import pdfplumber
import io
from pypdf import PdfReader
import os
import re

def clean_text(text: str) -> str:
    """
    Clean extracted text by removing OCR artifacts, non-printable characters, and normalizing whitespace.
    
    Args:
        text (str): Raw text extracted from PDF.
    
    Returns:
        str: Cleaned text.
    """
    # Remove non-printable characters (keep ASCII printable and newline/tab)
    text = re.sub(r'[^\x20-\x7E\n\t]', '', text)
    # Replace common OCR errors (e.g., '!' in place of 'l' or 'i')
    text = re.sub(r'(\w)![l1i](\w)', r'\1l\2', text)
    # Normalize multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    # Trim leading/trailing whitespace
    text = text.strip()
    return text

def extract_raw_json(file_stream: io.BytesIO) -> dict:
    """Extract all text from a PDF into raw JSON."""
    try:
        reader = PdfReader(file_stream)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        # Clean the extracted text
        cleaned_text = clean_text(text)
        return {"raw_text": cleaned_text}
    except Exception as e:
        return {"error": str(e)}

def pdf_to_json(pdf_path: str, json_path: str, use_raw: bool = False) -> None:
    """Convert PDF to JSON, either using pdfplumber (structured) or PyPDF2 (raw)."""
    data = {}
    
    if use_raw:
        # Use raw text extraction
        with open(pdf_path, 'rb') as file:
            file_stream = io.BytesIO(file.read())
            data = extract_raw_json(file_stream)
    else:
        # Use structured text extraction with pdfplumber
        data = {"pages": []}
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                # Clean the extracted text
                cleaned_text = clean_text(text) if text else ""
                page_data = {
                    "page_number": page_num,
                    "content": cleaned_text
                }
                data["pages"].append(page_data)
    
    # Save cleaned data to JSON file
    try:
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        print(f"Clean JSON created: {json_path}")
    except Exception as e:
        print(f"Error saving JSON: {e}")

def main():
    # Directory where your PDFs live
    pdf_dir = "airtable_attachments/attachments"
    # Create output folder
    out_dir = "json_output"
    os.makedirs(out_dir, exist_ok=True)

    # List the two PDF filenames you want to process
    pdf_files = [
        "invoice_rec2YTyfnPoBgjXMp.pdf",
        "Order_rec1nJMeDOHhOSMey.pdf"
    ]

    for fname in pdf_files:
        pdf_path = os.path.join(pdf_dir, fname)
        if not os.path.exists(pdf_path):
            print(f"Error: PDF file '{pdf_path}' not found. Skipping.")
            continue

        # Build the JSON output path, same base name but under json_output/
        base = os.path.splitext(fname)[0]
        json_path = os.path.join(out_dir, f"{base}.json")

        # Call your existing converter
        pdf_to_json(pdf_path, json_path, use_raw=False)
        print(f"→ Created JSON: {json_path}")

if __name__ == "__main__":
    main()