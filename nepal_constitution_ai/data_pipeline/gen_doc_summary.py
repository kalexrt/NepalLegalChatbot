import json
import glob  
import re
from tqdm import tqdm

def generate_doc_summary(ocr_json_folder_path):
    """
    Generate document summaries for all OCR JSON files in the specified folder.
    """
    # Define the number of pages to consider for generating a summary
    NUM_PAGES_TO_GENERATE_SUMMARY = 2
    ocr_json_files = glob.glob(f"{ocr_json_folder_path}/batch/*.json")
    ocr_json_files = sorted(ocr_json_files, key=lambda x: int(re.search(r'\d+', x).group()))

    for json_file in tqdm(ocr_json_files, "Generating document summaries"):
        # Load the batch JSON file
        with open(json_file, 'r') as file:
            docs = json.load(file)
        
        # Iterate through each document in the batch and generate summary
        for doc in docs:
            doc['summary'] = ""

            pages = doc['pages']

            if len(pages) >= NUM_PAGES_TO_GENERATE_SUMMARY:
                beginning_pages = pages[:NUM_PAGES_TO_GENERATE_SUMMARY]
            else:
                beginning_pages = pages

            # TODO: Call the LLM for summary generation and save it in doc['summary']
            raise NotImplementedError
        
        # Save the updated batch JSON file with summaries
        with open(json_file, 'w') as json_file:
            json.dump(docs, json_file, ensure_ascii=False, indent=4)