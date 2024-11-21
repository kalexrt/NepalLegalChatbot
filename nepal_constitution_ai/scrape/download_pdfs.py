import os
import json
import requests
from nepal_constitution_ai.config.config import settings


def download_file(url, folder_path, filename):
    """
    Download a file from the given URL and save it to the specified folder with the given filename.
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Downloaded: {filename}")
            return True
        else:
            print(f"Failed to download {filename}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False


def process_files(data, target_folder, missing_files):
    """
    Recursively process files in a nested JSON structure:
    - Download the file from the link.
    - Remove entries for missing files from the JSON if the download fails.
    """
    if isinstance(data, dict):
        keys_to_delete = []  # List to store keys for which entries should be removed
        for key, value in data.items():
            if isinstance(value, list) or isinstance(value, dict):
                # Recurse into nested structures
                process_files(value, target_folder, missing_files)
            elif key == "filename":
                filename = value.strip()
                target_file_path = os.path.join(target_folder, filename)

                # Download the file
                download_link = data.get("nep_pdf_link", "").strip()
                if download_link:
                    if download_file(download_link, target_folder, filename):
                        print(f"Downloaded: {filename}")
                    else:
                        # Mark the file as missing and add it to the missing_files list
                        missing_files.append(data)
                        keys_to_delete.append(key)
                else:
                    print(f"Missing download link for: {filename}")
                    missing_files.append(data)
                    keys_to_delete.append(key)

        # Remove missing files from the current level of the JSON structure
        for key in keys_to_delete:
            del data[key]

    elif isinstance(data, list):
        to_remove = []  # List to track items to remove
        for item in data:
            if isinstance(item, dict) or isinstance(item, list):
                # Recurse into nested structures
                process_files(item, target_folder, missing_files)
            else:
                to_remove.append(item)

        # Remove any completely empty items or invalid entries
        for item in to_remove:
            data.remove(item)

    return data


def main():
    # Paths
    JSON_PATH = f"{settings.DATA_PATH}/documents_info.json"  # Path to the JSON file
    TARGET_FOLDER = f"{settings.DATA_PATH}/downloaded_pdfs"  # Folder to store downloaded files

    # Load JSON data
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # List to keep track of missing files
    missing_files = []

    # Create target folder
    os.makedirs(TARGET_FOLDER, exist_ok=True)

    # Process files and remove missing entries from JSON
    updated_data = process_files(data, TARGET_FOLDER, missing_files)

    # Save the updated JSON back to the file, excluding missing entries
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)

    # Print summary
    print("\nProcessing Summary:")
    print(f"Files downloaded: {len(updated_data)}")
    print(f"Files missing and removed from JSON: {len(missing_files)}")

