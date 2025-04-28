import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in .env file.")
    sys.exit(1)
client = OpenAI(api_key=OPENAI_API_KEY)

# German to English keyword mappings for document type detection
KEYWORD_MAPPINGS = {
    "rechnung": "invoice", "bestellung": "order", "gesamtsumme": "total",
    "nettowert": "net_total", "bruttopreis": "gross_total", "lieferadresse": "delivery_address",
    "kundennummer": "customer_number", "bestellnummer": "order_number", "belegdatum": "issue_date",
    "liefertermin": "delivery_date", "artikel-nr": "article_code", "menge": "quantity",
    "preis": "price", "einheit": "unit", "firma": "company", "ansprechpartner": "contact_person",
    "email": "email", "straße": "street", "plz": "postal_code", "ort": "city"
}

# Define Invoice and Order Formats
INVOICE_FORMAT = {
    "logic": "Automate invoice processing. Output prices with exactly two decimal places.",
    "output": {
        "total_gross": "<float>",
        "total_net": "<float>",
        "business_name": "<string>",
        "items": [
            {
                "name": "<string>",
                "price": "<float>"
            }
        ]
    }
}

ORDER_FORMAT = {
    "logic": "Automate order requests. Output dates in DD.MM.YYYY format.",
    "output": {
        "buyer": {
            "buyer_company_name": "<string>",
            "buyer_person_name": "<string>",
            "buyer_email_address": "<string>"
        },
        "order": {
            "order_number": "<string>",
            "order_date": "<string>",
            "delivery": {
                "delivery_address_street": "<string>",
                "delivery_address_city": "<string>",
                "delivery_address_postal_code": "<string>"
            }
        },
        "product": [
            {
                "product_position": "<integer>",
                "product_article_code": "<string>",
                "product_quantity": "<integer>"
            }
        ]
    }
}

# Meta-Prompt (used directly as the prompt for gpt-4o)
META_PROMPT = """
You are tasked with generating an extraction prompt for processing a [DOCUMENT_TYPE] PDF to extract specific information and output it in a predefined JSON structure.

Where:
- `[DOCUMENT_TYPE]`: The type of document to process, e.g., "Invoice Document", "Order Document", or any other document type.
- `[LOGIC_INSTRUCTIONS]`: Specific instructions or logic for processing the document, such as formatting rules (e.g., "Output price with exactly two decimals" or "Output the date in formatting DD.MM.YYYY") or other processing guidelines.
- `[JSON_STRUCTURE]`: The desired output structure in JSON format, specifying the keys, value types (e.g., string, integer, float), and any nested objects or arrays.

### Instructions for Generating the Extraction Prompt
To create an effective and robust extraction prompt, adhere to the following best practices:

1. Clarity and Specificity: Craft a prompt that is unambiguous and clearly outlines the task for the extraction AI. Avoid vague language.
2. Contextual Awareness: Include details about the `[DOCUMENT_TYPE]` to provide context, such as where specific information might typically be located in such a document (e.g., headers, tables, footers).
3. Incorporate Logic: Fully integrate the `[LOGIC_INSTRUCTIONS]` into the prompt, ensuring all specified requirements (e.g., formatting, calculations) are explicitly stated.
4. Define Output Format: Precisely specify the output requirements using the `[JSON_STRUCTURE]`. Include details about data types and any formatting rules from the logic instructions.
5. Role Assignment: Begin the generated prompt with a role statement, such as "You are an AI assistant tasked with extracting information from a [DOCUMENT_TYPE] PDF," to set the tone and purpose.
6. Guidance for Extraction: Provide practical guidance on how to locate and extract each field in the `[JSON_STRUCTURE]`, such as suggesting common locations or keywords to look for in the document.
7. Handle Variations: Include instructions for the extraction AI to adapt to potential variations or inconsistencies in the document layout (e.g., different formats, missing fields), using general strategies like keyword searching or pattern recognition.

### Structure of the Generated Prompt
The prompt you generate should follow this structure:
- Opening Statement: "You are an AI assistant tasked with extracting information from a [DOCUMENT_TYPE] PDF."
- Task Description: Explain the goal, incorporating the `[LOGIC_INSTRUCTIONS]` to detail specific requirements.
- Extraction Details: List the information to extract, aligning with the keys and structure in `[JSON_STRUCTURE]`, and provide guidance on where or how to find each piece of data.
- Output Specification: State: "Output the extracted data in the following JSON format:" followed by the exact `[JSON_STRUCTURE]` provided in the input.
- Additional Instructions: Add tips for handling document-specific challenges or ensuring compliance with the logic instructions.
- Make sure the output is at least 1000 tokens long. 

IMPORTANT:
• Ensure that every numerical value is output as a number (not as a string).
• Follow the JSON structure exactly (including proper escaped characters for newlines and quotation marks).
• Do not include any extra fields or text outside the specified keys.
• Use of input format as whole when provided in the prompt.
• Donot ignore any information provided by the input format while generating the prompt. 

### Output
Your output should be the fully constructed extraction prompt as a single, cohesive text block, ready to be used by another AI model for PDF data extraction. Do not include additional commentary or explanations beyond the prompt itself unless explicitly requested.
"""

def detect_document_type(raw_json):
    """Detect if the document is an Invoice or Order based on JSON content."""
    raw_text = json.dumps(raw_json).lower()

    # Keyword-based detection
    invoice_keywords = ["rechnung", "gesamtsumme", "nettowert", "bruttopreis"]
    order_keywords = ["bestellung", "bestellnummer", "lieferadresse", "artikel-nr"]

    invoice_count = sum(1 for keyword in invoice_keywords if keyword in raw_text)
    order_count = sum(1 for keyword in order_keywords if keyword in raw_text)

    return "Invoice" if invoice_count >= order_count else "Order"

def generate_prompt(raw_json):
    """Generate a specialized prompt using OpenAI's gpt-4o model."""
    # Detect document type
    doc_type = detect_document_type(raw_json)
    
    # Select format based on document type
    doc_format = INVOICE_FORMAT if doc_type == "Invoice" else ORDER_FORMAT
    doc_type_name = "Invoice Document" if doc_type == "Invoice" else "Order Document"

    # Prepare the user message with document type and format
    user_message = (
        f"{META_PROMPT}\n\n"
        f"Generate an extraction prompt for a {doc_type_name} with the following details:\n"
        f"- DOCUMENT_TYPE: {doc_type_name}\n"
        f"- LOGIC_INSTRUCTIONS: {doc_format['logic']}\n"
        f"- JSON_STRUCTURE: {json.dumps(doc_format['output'], ensure_ascii=False, indent=2)}"
    )

    # Call OpenAI API to generate the specialized prompt
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a prompt engineering expert. Follow the provided meta-prompt to generate a specialized extraction prompt."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        generated_prompt = response.choices[0].message.content.strip()
        return generated_prompt, doc_type
    except Exception as e:
        return f"Error generating prompt: {str(e)}", doc_type

def main():
    """Main function to run the prompt generator."""
    # Specify the input JSON file path
    input_file = "json_output/Order_rec1nJMeDOHhOSMey.json"

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        sys.exit(1)

    try:
        # Read and parse JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_json = json.load(f)
        
        print(f"Processing file: {input_file}")

        # Generate prompt
        print("Generating prompt...")
        generated_prompt, doc_type = generate_prompt(raw_json)

        if "Error" in generated_prompt:
            print(generated_prompt)
            sys.exit(1)

        # Display results
        print(f"\nDetected Document Type: {doc_type}")
        print("\nGenerated Prompt:")
        print("-" * 50)
        print(generated_prompt)
        print("-" * 50)

        # Save the generated prompt to a file
        output_dir = "generated_prompts"
        os.makedirs(output_dir, exist_ok=True)
        prompt_filename = os.path.join(output_dir, f"{doc_type.lower()}_prompt.txt")
        with open(prompt_filename, 'w', encoding='utf-8') as f:
            f.write(generated_prompt)
        print(f"\nPrompt saved to: {prompt_filename}")

    except json.JSONDecodeError:
        print("Error: Invalid JSON file. Please provide a valid JSON file.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

