from openai import OpenAI  # New import for v1.0.0+

class InvoiceProcessor:
    def __init__(self, api_key: str, output_dir: str = "processed_results"):
        """Initialize the invoice processor with API key and output directory"""
        self.api_key = api_key
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.client = OpenAI(api_key=self.api_key)  # New client initialization

    def extract_invoice_data(self, text: str, max_retries: int = 3) -> Optional[Dict]:
        """Use GPT-4 to extract structured invoice data with new API syntax"""
        prompt = f"""
        Analyze the following invoice document and extract the following information in JSON format:
        - total_gross (as float with 2 decimals)
        - total_net (as float with 2 decimals) 
        - business_name (as string)
        - items (list of objects with name and price)
        
        Important rules:
        1. Price values must have exactly two decimal places (e.g., 12.50 not 12.5)
        2. If any value is missing, use null
        3. Clean business names by removing addresses or extra information
        
        Invoice Text:
        {text}
        
        Output must be valid JSON following this exact format:
        {{
          "total_gross": float,
          "total_net": float,
          "business_name": "string",
          "items": [
            {{
              "name": "string",
              "price": float
            }}
          ]
        }}
        """
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(  # New API syntax
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert at extracting structured data from invoices. Follow all instructions precisely."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    timeout=30
                )
                
                result = response.choices[0].message.content
                
                # Handle JSON wrapped in markdown code blocks
                if result.startswith("```json"):
                    result = result[result.find("{") : result.rfind("}") + 1]
                elif result.startswith("```"):
                    result = result[result.find("{") : result.rfind("}") + 1]
                
                # Parse and validate the JSON
                json_data = json.loads(result)
                
                # Validate required fields
                if not all(key in json_data for key in ["total_gross", "total_net", "business_name", "items"]):
                    raise ValueError("Missing required fields in JSON response")
                
                return json_data
                
            except json.JSONDecodeError as e:
                logging.warning(f"Failed to parse JSON (attempt {attempt + 1}): {str(e)}")
                time.sleep(2)
            except Exception as e:
                logging.error(f"Error processing invoice (attempt {attempt + 1}): {str(e)}")
                time.sleep(5)
        
        logging.error(f"Failed to process invoice after {max_retries} attempts")
        return None