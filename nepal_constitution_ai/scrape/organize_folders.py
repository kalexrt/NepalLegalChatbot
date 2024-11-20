import os
import json
import shutil

def organize_pdfs_from_json(json_data, base_key, pdf_source_folder, target_base_folder, summary):
    """
    Recursively process a JSON object to organize PDFs into categorized folders.

    Args:
        json_data (dict or list): JSON data to process.
        base_key (str): The current base key for folder naming.
        pdf_source_folder (str): Folder containing all PDFs.
        target_base_folder (str): Base folder where categorized folders will be created.
        summary (dict): Summary dictionary to record copied and missing files.
    """
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            new_base_key = os.path.join(base_key, key)  # Update folder path
            organize_pdfs_from_json(value, new_base_key, pdf_source_folder, target_base_folder, summary)
    elif isinstance(json_data, list):
        # Create the folder for this level
        category_folder = os.path.join(target_base_folder, base_key)
        os.makedirs(category_folder, exist_ok=True)

        if base_key not in summary:
            summary[base_key] = {"copied": [], "missing": []}

        for doc in json_data:
            filename = doc.get("filename")
            if filename:
                source_file_path = os.path.join(pdf_source_folder, filename)
                target_file_path = os.path.join(category_folder, filename)

                if os.path.exists(source_file_path):
                    # Copy the file to the category folder
                    shutil.copy(source_file_path, target_file_path)
                    summary[base_key]["copied"].append(filename)
                else:
                    # File not found in the source folder
                    summary[base_key]["missing"].append(filename)


def organize_pdfs(json_file, pdf_source_folder, target_base_folder):
    """
    Organize PDFs into folders based on a JSON file with potential nested keys.

    Args:
        json_file (str): Path to the JSON file.
        pdf_source_folder (str): Path to the folder containing all PDFs.
        target_base_folder (str): Path to the folder where categorized folders will be created.

    Returns:
        dict: Summary of copied and missing files.
    """
    # Load the JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Initialize summary dictionary
    summary = {}

    # Process the JSON recursively
    organize_pdfs_from_json(data, "", pdf_source_folder, target_base_folder, summary)

    # Print summary
    total_files = sum(len(v["copied"]) + len(v["missing"]) for v in summary.values())
    copied_files = sum(len(v["copied"]) for v in summary.values())
    missing_files = sum(len(v["missing"]) for v in summary.values())

    print(f"Total files referenced in JSON: {total_files}")
    print(f"Files copied: {copied_files}")
    print(f"Files missing: {missing_files}")
    

def main():
    DATA_PATH = "data"
    JSON_FILE = f"{DATA_PATH}/documents_info.json"  # Path to the JSON file
    PDF_SOURCE_FOLDER = f"{DATA_PATH}/downloaded_pdfs"  # Path to the folder containing all PDFs
    TARGET_BASE_FOLDER = f"{DATA_PATH}/organized_pdfs"  # Path to the base folder for categorized PDFs

    os.makedirs(TARGET_BASE_FOLDER, exist_ok=True)
    organize_pdfs(JSON_FILE, PDF_SOURCE_FOLDER, TARGET_BASE_FOLDER)
