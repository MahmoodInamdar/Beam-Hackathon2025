import os
import re
import json
import logging
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# ------------------- Configuration -------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set your OPENAI_API_KEY in .env or environment")

client      = OpenAI(api_key=OPENAI_API_KEY)
BASE_DIR    = Path("/Users/maple/Downloads/beam")
PDF_DIR     = BASE_DIR / "airtable_attachments/attachments"
PROMPT_DIR  = BASE_DIR / "generated_prompts"
OUTPUT_DIR  = BASE_DIR / "test_output"
OUTPUT_JSON = OUTPUT_DIR / "extracted_data.json"

for d in (PDF_DIR, PROMPT_DIR):
    if not d.is_dir():
        raise FileNotFoundError(f"Required directory not found: {d}")
OUTPUT_DIR.mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# ------------------- Utility Functions -------------------

def load_prompt_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()

INVOICE_PROMPT = load_prompt_file(PROMPT_DIR / "invoice_prompt.txt")
ORDER_PROMPT   = load_prompt_file(PROMPT_DIR / "order_prompt.txt")

def normalize_number(txt: str):
    if not txt:
        return None
    s = txt.replace("€","").replace("$","").replace("£","").strip()
    s = re.sub(r'(?<=\d)\.(?=\d{3}\b)', '', s)
    s = s.replace(",", ".")
    try:
        return round(float(s), 2)
    except:
        return None

def normalize_date(txt: str):
    if not txt:
        return None
    m = re.match(r'(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})', txt)
    if m:
        d,mo,y = m.groups()
        return f"{int(d):02d}.{int(mo):02d}.{y}"
    return txt



def extract_pdf_text_with_ocr(path: Path) -> str:
    out_lines = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    out_lines.append(text)
                for table in page.extract_tables():
                    for row in table:
                        cells = [c.strip() for c in row if c]
                        if cells:
                            out_lines.append(" | ".join(cells))
    except Exception as e:
        logging.warning(f"pdfplumber error in {path.name}: {e}")
        text = ""

    result = "\n".join(out_lines).strip()
    if result:
        return result

    
    try:
        logging.info(f"OCR fallback for {path.name}")
        images = convert_from_path(str(path))
        ocr_txt = []
        for img in images:
            ocr = pytesseract.image_to_string(img, lang="deu+eng")
            if ocr.strip():
                ocr_txt.append(ocr)
        return "\n".join(ocr_txt).strip()
    except Exception as e:
        logging.error(f"OCR failed for {path.name}: {e}")
        return ""


def call_gpt4o(prompt_template: str, text: str) -> dict:
    if "{text}" in prompt_template:
        user_content = prompt_template.format(text=text)
    else:
        user_content = (
            prompt_template
            + "\n\nExtract from the following text:\n```\n"
            + text
            + "\n```"
        )

    messages = [
        {"role": "system", "content": "You are a precise data extraction assistant. Output *ONLY* a JSON object."},
        {"role": "user",   "content": user_content}
    ]

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.0,
        max_tokens=1000
    )

    raw = resp.choices[0].message.content.strip()
    if not raw:
        logging.error("Empty reply from GPT-4o")
        return None

    
    cleaned = re.sub(
        r"^```(?:json)?\s*([\s\S]*?)\s*```$",
        r"\1",
        raw,
        flags=re.IGNORECASE
    )

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logging.error("Failed to parse JSON. Reply after fence-stripping:")
        logging.error(cleaned)
        return None

def post_process(data: dict) -> dict:
    if "total_gross" in data:
        data["total_gross"] = normalize_number(str(data["total_gross"]))
    if "total_net" in data:
        data["total_net"] = normalize_number(str(data["total_net"]))
    if "items" in data:
        for it in data["items"]:
            it["price"] = normalize_number(str(it.get("price")))
    if "order_date" in data:
        data["order_date"] = normalize_date(str(data["order_date"]))
    if "product" in data:
        prods = data.pop("product")
        if isinstance(prods, dict):
            prods = [prods]
        data["products"] = []
        for p in prods:
            data["products"].append({
                "product_position": int(p.get("product_position", 0)),
                "product_article_code": str(p.get("product_article_code","")),
                "product_quantity": int(p.get("product_quantity", 0))
            })
    return data



def main():
    records, processed, failed, skipped, ocr_used = [], [], [], [], []

    all_pdfs = list(PDF_DIR.glob("*.pdf"))
    logging.info(f"Total PDF files found: {len(all_pdfs)}")

    for pdf_file in sorted(all_pdfs):
        fname = pdf_file.name
        lfname = fname.lower()
        if "invoice" in lfname:
            prompt  = INVOICE_PROMPT
            dataset = "Invoice"
        elif "order" in lfname:
            prompt  = ORDER_PROMPT
            dataset = "Order"
        else:
            skipped.append(fname)
            continue

        processed.append(fname)
        logging.info(f"Processing {fname} as {dataset}")
        text = extract_pdf_text_with_ocr(pdf_file)
        if not text:
            logging.warning(f"No text (even after OCR) for {fname}")
            failed.append(fname)
            continue

        extracted = call_gpt4o(prompt, text)
        if not extracted:
            logging.warning(f"Extraction failed for {fname}")
            failed.append(fname)
            continue

        extracted = post_process(extracted)
        records.append({
            "File ID": pdf_file.stem,
            "Dataset": dataset,
            "File": pdf_file.name,
            "Expected Output": json.dumps(extracted, ensure_ascii=False, indent=2)
        })

    # Write out results
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # Diagnostics
    logging.info(f"Wrote {len(records)} records to {OUTPUT_JSON}")
    logging.info(f"Processed: {len(processed)} | Success: {len(records)} | Failed: {len(failed)} | Skipped: {len(skipped)}")
    if failed:
        logging.info("Failed files: " + ', '.join(failed))
    if skipped:
        logging.info("Skipped files (no 'invoice' or 'order' in filename): " + ', '.join(skipped))

if __name__ == "__main__":
    main()