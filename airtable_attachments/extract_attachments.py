# import requests
# import os
# from dotenv import load_dotenv
# import urllib.request

# # Load environment variables
# load_dotenv()
# pat = os.getenv("AIRTABLE_PAT")  # Use PAT instead of API key
# base_id = "appKKaECsy1sYtE5V"
# table_id = "tblU22DmmdsrMBXh1"
# view_id = "viwpa8gwXriMoB1i8"

# # Create a folder for attachments
# output_dir = "attachments"
# os.makedirs(output_dir, exist_ok=True)

# # Airtable API endpoint
# url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
# headers = {"Authorization": f"Bearer {pat}"}  # Updated to use PAT
# params = {"view": view_id}

# def download_attachment(url, filename, output_dir):
#     """Download an attachment and save it to the output directory."""
#     try:
#         # Clean filename to avoid invalid characters
#         filename = "".join(c for c in filename if c.isalnum() or c in ('.', '_', '-'))
#         filepath = os.path.join(output_dir, filename)
#         urllib.request.urlretrieve(url, filepath)
#         print(f"Downloaded: {filepath}")
#     except Exception as e:
#         print(f"Error downloading {filename}: {e}")

# def fetch_records():
#     """Fetch all records from the Airtable view."""
#     records = []
#     offset = None

#     while True:
#         # Include offset in params if it exists
#         if offset:
#             params["offset"] = offset
        
#         response = requests.get(url, headers=headers, params=params)
#         response.raise_for_status()  # Raise an error for bad responses
#         data = response.json()
        
#         records.extend(data["records"])
#         offset = data.get("offset")
        
#         if not offset:
#             break
    
#     return records

# def process_attachments(records):
#     """Process attachments from records."""
#     for record in records:
#         fields = record["fields"]
#         print(f"Processing record: {record['id']}")
        
#         # Loop through fields to find attachments
#         for field_name, field_value in fields.items():
#             if isinstance(field_value, list) and field_value and "url" in field_value[0]:
#                 # This field contains attachments
#                 print(f"Found attachments in field '{field_name}':")
#                 for attachment in field_value:
#                     attachment_url = attachment["url"]
#                     filename = attachment.get("filename", f"attachment_{attachment['id']}")
#                     print(f" - {filename} ({attachment_url})")
#                     download_attachment(attachment_url, filename, output_dir)

# def main():
#     try:
#         print("Fetching records from Airtable...")
#         records = fetch_records()
#         print(f"Fetched {len(records)} records.")
#         process_attachments(records)
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     main()


import requests
import os
import pandas as pd
from dotenv import load_dotenv
import urllib.request
import json

# Load environment variables
load_dotenv()
pat = os.getenv("AIRTABLE_PAT")  # Personal Access Token
base_id = "appKKaECsy1sYtE5V"
table_id = "tblU22DmmdsrMBXh1"
view_id = "viwpa8gwXriMoB1i8"

# Create folders for attachments and output
attachments_dir = "attachments"
os.makedirs(attachments_dir, exist_ok=True)
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Airtable API endpoint
url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
headers = {"Authorization": f"Bearer {pat}"}
params = {"view": view_id}

def download_attachment(url, filename, output_dir):
    """Download an attachment and save it to the output directory."""
    try:
        # Clean filename to avoid invalid characters
        filename = "".join(c for c in filename if c.isalnum() or c in ('.', '_', '-'))
        filepath = os.path.join(output_dir, filename)
        urllib.request.urlretrieve(url, filepath)
        print(f"Downloaded: {filepath}")
        return filename  # Return the cleaned filename
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return None

def fetch_records():
    """Fetch all records from the Airtable view."""
    records = []
    offset = None

    while True:
        if offset:  # Fixed: Removed 'Occupationally' and redundant 'if'
            params["offset"] = offset
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        
        records.extend(data["records"])
        offset = data.get("offset")
        
        if not offset:
            break
    
    return records

def process_records(records):
    """Process records and extract all fields, including attachments."""
    data = []
    
    for record in records:
        fields = record["fields"]
        record_data = {
            "File ID": fields.get("File ID", ""),
            "Expected Output": fields.get("Expected Output", ""),
            "Dataset": fields.get("Dataset", ""),
            "File": ""  # Will store attachment filename(s)
        }
        
        # Handle attachments in the 'File' field
        attachments = fields.get("File", [])
        if attachments:
            attachment_filenames = []
            for attachment in attachments:
                attachment_url = attachment.get("url")
                filename = attachment.get("filename", f"attachment_{attachment['id']}")
                saved_filename = download_attachment(attachment_url, filename, attachments_dir)
                if saved_filename:
                    attachment_filenames.append(saved_filename)
            record_data["File"] = "; ".join(attachment_filenames)  # Join multiple filenames with semicolon
        
        data.append(record_data)
    
    return data

def save_to_csv(data, output_path):
    """Save data to a CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Saved data to {output_path}")

def save_to_json(data, output_path):
    """Save data to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved data to {output_path}")

def main():
    try:
        print("Fetching records from Airtable...")
        records = fetch_records()
        print(f"Fetched {len(records)} records.")
        
        print("Processing records and downloading attachments...")
        data = process_records(records)
        
        # Save to CSV
        csv_path = os.path.join(output_dir, "airtable_data.csv")
        save_to_csv(data, csv_path)
        
        # Save to JSON
        json_path = os.path.join(output_dir, "airtable_data.json")
        save_to_json(data, json_path)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()