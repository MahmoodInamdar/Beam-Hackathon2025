# import os
# import json
# import pdfplumber
# from openai import OpenAI
# from pathlib import Path

# # Configuration
# PDF_DIR = "airtable_attachments/attachments"
# OUTPUT_DIR = "test_output"
# OUTPUT_JSON = os.path.join(OUTPUT_DIR, "extracted_data.json")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set your OpenAI API key as an environment variable

# # Initialize OpenAI client
# client = OpenAI(api_key=OPENAI_API_KEY)

# # Define prompts as provided
# INVOICE_PROMPT = """You are an AI assistant tasked with extracting information from an Invoice Document PDF. Your goal is to automate invoice processing by extracting specific details and formatting them according to the given instructions. Ensure that all prices are output with exactly two decimal places.

# To achieve this, locate and extract the following information:

# 1. **Total Gross**: Look for the total gross amount, often found near the bottom of the invoice, typically labeled as "Total Gross" or "Gross Amount". Extract this as an integer.

# 2. **Total Net**: Identify the total net amount, which is usually listed alongside the gross total, often labeled as "Total Net" or "Net Amount". Extract this as an integer.

# 3. **Business Name**: Find the name of the business issuing the invoice. This is usually located at the top of the document, possibly in the header, and may be labeled as "Business Name" or simply be the prominent name on the document. Extract this as a string.

# 4. **Items**: Extract details of each item listed on the invoice. This information is typically found in a table format. For each item, extract:
#    - **Name**: The name or description of the item, usually in the first column of the table. Extract this as a string.
#    - **Price**: The price of the item, often found in the same row as the item name, in a column labeled "Price" or "Amount". Ensure the price is extracted as a float with exactly two decimal places.

# Output the extracted data in the following JSON format:
# ```json
# {
#   "total_gross": "<float>",
#   "total_net": "<float>",
#   "business_name": "<string>",
#   "items": [
#     {
#       "name": "<string>",
#       "price": "<float>"
#     }
#   ]
# }
# ```

# For documents with variations in layout, use keyword searching and pattern recognition to locate the required fields. Adapt to different formats by identifying common labels and structures associated with the information you need to extract."""

# ORDER_PROMPT = """You are an AI assistant tasked with extracting information from an Order Document PDF. Your goal is to automate order requests by extracting specific details and formatting dates in the DD.MM.YYYY format.

# To achieve this, you need to locate and extract the following information from the Order Document:

# 1. **Buyer Information**:
#    - **Buyer Company Name**: Typically found in the header or contact section of the document.
#    - **Buyer Person Name**: Look for names associated with the buyer company, often near the company name.
#    - **Buyer Email Address**: Search for email patterns, usually found in the contact details section.

# 2. **Order Information**:
#    - **Order Number**: This is often labeled as "Order No." or similar, usually near the top of the document.
#    - **Order Date**: Look for a date associated with the order, ensuring it is formatted as DD.MM.YYYY.

# 3. **Delivery Information**:
#    - **Delivery Address Street**: Typically found in the delivery section, often labeled as "Street" or "Address".
#    - **Delivery Address City**: Look for the city name in the delivery section.
#    - **Delivery Address Postal Code**: Usually follows the city name in the delivery section.

# 4. **Product Information**:
#    - For each product listed, extract:
#      - **Product Position**: This is the order in which the product appears in the list, starting from 1.
#      - **Product Article Code**: Look for codes associated with each product, often labeled as "Article Code" or similar.
#      - **Product Quantity**: Find the quantity ordered, typically listed alongside the product details.

# Output the extracted data in the following JSON format:

# ```json
# {
#   "buyer": {
#     "buyer_company_name": "<string>",
#     "buyer_person_name": "<string>",
#     "buyer_email_address": "<string>"
#   },
#   "order": {
#     "order_number": "<string>",
#     "order_date": "<string>",
#     "delivery": {
#       "delivery_address_street": "<string>",
#       "delivery_address_city": "<string>",
#       "delivery_address_postal_code": "<string>"
#     }
#   },
#   "product": [
#     {
#       "product_position": "<integer>",
#       "product_article_code": "<string>",
#       "product_quantity": "<integer>"
#     }
#   ]
# }
# ```

# In case of variations in document layout, use keyword searching and pattern recognition to locate the required fields. Adapt to different formats by focusing on common labels and structures associated with each data type."""

# # Extract text from PDF
# def extract_pdf_text(file_path):
#     try:
#         with pdfplumber.open(file_path) as pdf:
#             text = ""
#             for page in pdf.pages:
#                 page_text = page.extract_text()
#                 if page_text:
#                     text += page_text + "\n"
#             return text.strip()
#     except Exception as e:
#         print(f"Error extracting text from {file_path}: {e}")
#         return ""

# # Use GPT-4o to extract data from text
# def extract_data_with_gpt4o(text, prompt):
#     try:
#         # Combine prompt and extracted text
#         # *** Using the provided prompt directly here ***
#         full_prompt = f"{prompt}\n\nExtracted Text:\n{text}"

#         # Call GPT-4o
#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=[
#                 {"role": "user", "content": full_prompt}
#             ],
#             response_format={"type": "json_object"}  # Ensure JSON output
#         )

#         # Parse the response
#         extracted_data = json.loads(response.choices[0].message.content)

#         # Post-process to match airtable_data.json format
#         if "total_gross" in extracted_data and isinstance(extracted_data["total_gross"], int):
#             extracted_data["total_gross"] = float(extracted_data["total_gross"]) / 100  # Convert integer to float (e.g., 1264 -> 12.64)
#         if "total_net" in extracted_data and isinstance(extracted_data["total_net"], int):
#             extracted_data["total_net"] = float(extracted_data["total_net"]) / 100  # Convert integer to float (e.g., 1062 -> 10.62)
#         if "product" in extracted_data:
#             # Rename "product" to "products" and ensure it's a list
#             products = extracted_data.pop("product")
#             if isinstance(products, dict):
#                 products = [products]  # Convert single product object to list
#             extracted_data["products"] = products

#         return extracted_data

#     except Exception as e:
#         print(f"Error processing with GPT-4o: {e}")
#         return None

# # Process a single PDF
# def process_pdf(file_path, dataset):
#     # Extract text from PDF
#     text = extract_pdf_text(file_path)
#     if not text:
#         print(f"No text extracted from {file_path}")
#         return None

#     # Select prompt based on dataset
#     # *** Selecting the provided INVOICE_PROMPT or ORDER_PROMPT here ***
#     prompt = INVOICE_PROMPT if dataset == "Invoice" else ORDER_PROMPT
#     if not prompt:
#         print(f"No prompt available for {dataset}")
#         return None

#     # Extract data using GPT-4o
#     extracted_data = extract_data_with_gpt4o(text, prompt)
#     if not extracted_data:
#         print(f"Failed to extract data from {file_path}")
#         return None

#     # Prepare output
#     file_id = Path(file_path).stem
#     output_data = {
#         "File ID": file_id,
#         "Dataset": dataset,
#         "File": Path(file_path).name,
#         "Expected Output": json.dumps(extracted_data, indent=2, ensure_ascii=False)
#     }

#     return output_data

# # Main function to process all PDFs
# def main():
#     # Validate setup
#     if not os.path.exists(PDF_DIR):
#         print(f"Directory {PDF_DIR} does not exist.")
#         return

#     if not OPENAI_API_KEY:
#         print("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.")
#         return

#     if not INVOICE_PROMPT or not ORDER_PROMPT:
#         print("One or both prompts are empty.")
#         return

#     # Create output directory if it doesn't exist
#     os.makedirs(OUTPUT_DIR, exist_ok=True)

#     results = []
#     for filename in os.listdir(PDF_DIR):
#         if filename.lower().endswith('.pdf'):
#             file_path = os.path.join(PDF_DIR, filename)
#             # Determine dataset based on filename prefix
#             dataset = "Invoice" if filename.startswith("invoice_") else "Order"
#             result = process_pdf(file_path, dataset)
#             if result:
#                 results.append(result)

#     # Save results to JSON file
#     with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
#         json.dump(results, f, indent=2, ensure_ascii=False)
    
#     print(f"Extraction complete. Results saved to {OUTPUT_JSON}")

# if __name__ == "__main__":
#     main()

import os
import json
import pdfplumber
from openai import OpenAI
from pathlib import Path
from sklearn.metrics import accuracy_score
import numpy as np
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
BASE_DIR = "/Users/maple/Downloads/beam"
PDF_DIR = os.path.join(BASE_DIR, "airtable_attachments/attachments")
OUTPUT_DIR = os.path.join(BASE_DIR, "test_output")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "extracted_data.json")
AIRTABLE_JSON = os.path.join(BASE_DIR, "airtable_attachments/output/airtable_data.json")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
if not OPENAI_API_KEY:
    logging.error("OpenAI API key not set. Set OPENAI_API_KEY environment variable.")
    exit(1)
client = OpenAI(api_key=OPENAI_API_KEY)

# Refined Prompts
import os


# path to the previously generated prompt
PROMPT_DIR = "generated_prompts"
INVOICE_PROMPT_FILE = os.path.join(PROMPT_DIR, "invoice_prompt.txt")
ORDER_PROMPT_FILE = os.path.join(PROMPT_DIR, "order_prompt.txt")

def load_invoice_prompt(path: str) -> str:
    """
    Reads and returns the contents of the invoice prompt file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Invoice prompt file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# Load it once at startup
INVOICE_PROMPT = load_invoice_prompt(INVOICE_PROMPT_FILE)
ORDER_PROMPT = load_invoice_prompt(ORDER_PROMPT_FILE)

# Utility Functions
def normalize_number(text):
    """Convert text number to float with two decimal places."""
    if not text:
        return None
    # Remove currency symbols and whitespace
    text = re.sub(r'[€$£]', '', text.strip())
    # Handle comma/decimal separators
    text = re.sub(r'(\d)\.(\d{3}),', r'\1\2.', text)  # e.g., 1.234,56 -> 1234.56
    text = re.sub(r',(\d{2})$', r'.\1', text)  # e.g., 1234,56 -> 1234.56
    try:
        return round(float(text), 2)
    except ValueError:
        return None

def normalize_date(text):
    """Convert date to DD.MM.YYYY format."""
    if not text:
        return None
    # Common date patterns
    patterns = [
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
        r'(\d{1,2})/(\d{1,2})/(\d{4})',   # DD/MM/YYYY
        r'(\d{1,2})-(\d{1,2})-(\d{4})',   # DD-MM-YYYY
        r'(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(\d{4})'  # DD Mon YYYY
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            day, month, year = match.groups()
            if month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
                month_map = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                             'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
                month = month_map[month[:3].capitalize()]
            return f"{int(day):02d}.{int(month):02d}.{year}"
    return None

# Extract text and tables from PDF
def extract_pdf_text(file_path):
    """Extract text and tables from a PDF."""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                # Extract raw text
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                # Extract tables for items/products
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        text += " | ".join(str(cell) for cell in row if cell) + "\n"
            return text.strip()
    except Exception as e:
        logging.error(f"Error extracting text from {file_path}: {e}")
        return ""

# Extract data with GPT-4o
def extract_data_with_gpt4o(text, prompt):
    """Extract structured data using GPT-4o."""
    try:
        full_prompt = prompt.format(text=text)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant."},
                {"role": "user", "content": full_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        extracted_data = json.loads(response.choices[0].message.content)

        # Post-process for accuracy
        if "total_gross" in extracted_data:
            extracted_data["total_gross"] = normalize_number(str(extracted_data["total_gross"]))
        if "total_net" in extracted_data:
            extracted_data["total_net"] = normalize_number(str(extracted_data["total_net"]))
        if "items" in extracted_data:
            for item in extracted_data["items"]:
                if "price" in item:
                    item["price"] = normalize_number(str(item["price"]))
        if "order_date" in extracted_data:
            extracted_data["order_date"] = normalize_date(extracted_data["order_date"])
        if "product" in extracted_data:
            products = extracted_data.pop("product")
            if isinstance(products, dict):
                products = [products]
            extracted_data["products"] = [
                {
                    "product_position": int(p["product_position"]),
                    "product_article_code": str(p["product_article_code"]),
                    "product_quantity": int(p["product_quantity"])
                } for p in products
            ]

        return extracted_data
    except Exception as e:
        logging.error(f"Error processing with GPT-4o: {e}")
        return None

# Process a single PDF
def process_pdf(file_path, dataset):
    """Process a single PDF and extract data."""
    text = extract_pdf_text(file_path)
    if not text:
        logging.warning(f"No text extracted from {file_path}")
        return None

    prompt = INVOICE_PROMPT if dataset == "Invoice" else ORDER_PROMPT
    extracted_data = extract_data_with_gpt4o(text, prompt)
    if not extracted_data:
        logging.warning(f"Failed to extract data from {file_path}")
        return None

    file_id = Path(file_path).stem
    output_data = {
        "File ID": file_id,
        "Dataset": dataset,
        "File": Path(file_path).name,
        "Expected Output": json.dumps(extracted_data, indent=2, ensure_ascii=False)
    }
    return output_data

# Flatten dictionary for evaluation
def flatten_dict(d, parent_key='', sep='_'):
    """Flatten a nested dictionary."""
    items = []
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}_{i}", sep).items())
                else:
                    items.append((f"{new_key}_{i}", item))
        else:
            items.append((new_key, value))
    return dict(items)

# Evaluate accuracy
def evaluate_accuracy(airtable_path, extracted_path):
    """Compute accuracy score between two JSON datasets."""
    try:
        with open(airtable_path, 'r', encoding='utf-8') as f:
            airtable_data = json.load(f)
        with open(extracted_path, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)

        airtable_map = {}
        for record in airtable_data:
            file_id = record.get('File ID')
            try:
                airtable_map[file_id] = json.loads(record['Expected Output'])
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in Expected Output for File ID {file_id} in {airtable_path}: {e}")
                return {'error': f"Invalid JSON in Expected Output for File ID {file_id}"}

        extracted_map = {}
        for record in extracted_data:
            file_id = record.get('File ID')
            try:
                extracted_map[file_id] = json.loads(record['Expected Output'])
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in Expected Output for File ID {file_id} in {extracted_path}: {e}")
                return {'error': f"Invalid JSON in Expected Output for File ID {file_id}"}

        true_values = []
        pred_values = []
        for file_id in extracted_map:
            if file_id not in airtable_map:
                logging.warning(f"File ID {file_id} not found in airtable_data")
                continue
            flat_true = flatten_dict(airtable_map[file_id])
            flat_pred = flatten_dict(extracted_map[file_id])
            for key in flat_true:
                true_val = flat_true.get(key)
                pred_val = flat_pred.get(key)
                true_values.append(str(true_val) if true_val is not None else '')
                pred_values.append(str(pred_val) if pred_val is not None else '')

        if not true_values:
            logging.error("No matching records or fields found")
            return {'error': 'No matching records or fields found'}

        accuracy = accuracy_score(true_values, pred_values)
        return {
            'accuracy': accuracy,
            'fields_compared': len(true_values),
            'matched_records': len([fid for fid in extracted_map if fid in airtable_map])
        }
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        return {'error': f"File not found - {e}"}
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format: {e}")
        return {'error': f"Invalid JSON format - {e}"}
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return {'error': f"Unexpected error - {e}"}

# Main function
def main():
    if not os.path.exists(PDF_DIR):
        logging.error(f"Directory {PDF_DIR} does not exist")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []
    for filename in os.listdir(PDF_DIR):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(PDF_DIR, filename)
            dataset = "Invoice" if filename.lower().startswith("invoice_") else "Order"
            logging.info(f"Processing {filename} as {dataset}")
            result = process_pdf(file_path, dataset)
            if result:
                results.append(result)

    if results:
        try:
            with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logging.info(f"Results saved to {OUTPUT_JSON}")

            eval_results = evaluate_accuracy(AIRTABLE_JSON, OUTPUT_JSON)
            logging.info("Evaluation Results:")
            logging.info(json.dumps(eval_results, indent=2))
        except Exception as e:
            logging.error(f"Error saving or evaluating results: {e}")
    else:
        logging.warning("No PDFs processed successfully")

if __name__ == "__main__":
    main()