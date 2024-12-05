import os
import json

def filter_existing_laws(existing_laws_json_file, ocr_json_folder, output_json_folder):
    # Ensure the output folder exists
    os.makedirs(output_json_folder, exist_ok=True)

    # Get list of PDFs
    with open(existing_laws_json_file, "r") as f:
        existing_laws_json = json.load(f)
        pdf_files = existing_laws_json["existing_laws"]

    # Iterate through JSON files
    for json_file in os.listdir(ocr_json_folder):
        if json_file.endswith(".json"):
            json_path = os.path.join(ocr_json_folder, json_file)
            
            # Load JSON data
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Keep only matching entries
            new_entries = [entry for entry in data if entry.get("filename") in pdf_files]

            # Save the updated JSON
            output_path = os.path.join(output_json_folder, f"filtered_{json_file}")
            with open(output_path, 'w') as f:
                json.dump(new_entries, f, ensure_ascii=False, indent=4)

    print("Processing complete. Filtered JSON files are saved in:", output_json_folder)