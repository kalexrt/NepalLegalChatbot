from pdf2image import convert_from_path
from tqdm import tqdm
import numpy as np
import easyocr
import torch
import time
import glob
import json
import os
import re

# Initialize EasyOCR reader
if torch.cuda.is_available():
    reader = easyocr.Reader(['ne', 'en'], gpu=True)  # Enable GPU if available
else:
    reader = easyocr.Reader(['ne', 'en'], gpu=False)  # Use CPU if GPU is not available

nepali_pattern = re.compile(r'[\u0900-\u097F\u0966-\u096F\[\]\(\)\{\},]+') # Checks if the string contains Nepali characters

def extract_title(lines):
    doc_title = ""
    for line in lines:
        if line.strip():  # Check if the line is not blank
            # Split the line by space and check if it has more than two words
            if len(line.strip().split()) > 1 and all(len(word) > 2 for word in line.strip().split()) and nepali_pattern.search(line):
                doc_title = line.strip()
                break
    return doc_title

def pdf_to_nepali_text(pdf_path):
    pages = []
    doc_lines = []
    images = convert_from_path(pdf_path)
    filename = pdf_path.split("/")[-1]
    start_time = time.time()

    for image in images:
        # Crop out the top and bottom areas
        width, height = image.size
        margin = int(0.06*height)
        cropped_image = image.crop((0, margin, width, height - margin))
        # Read text with bounding box details
        image_np = np.array(cropped_image)
        results = reader.readtext(image_np)
        
        # Sort the results line by line, and within each line, left to right
        results_sorted = sorted(results, key=lambda x: (x[0][0][1], x[0][0][0]))

        page_text = ''
        page_lines = []
        current_line_y = results_sorted[0][0][0][1]
        line_text = []

        for box, text, _ in results_sorted:
            y_coord = box[0][1]
            
            # Start a new line if the Y-coordinate differs significantly from the previous line
            gap = abs(y_coord - current_line_y)
            if gap > 10:  # Adjust threshold as needed
                page_text += ' '.join(line_text)
                page_lines.append((' '.join(line_text)).strip())
                if gap > 140:
                    page_text += "\n"
                    page_lines.append("\n")
                
                line_text = []
                current_line_y = y_coord

            line_text.append(text)

        page_lines.append((' '.join(line_text)).strip())
        page_text += ' '.join(line_text)  # Add the last line

        # Cleaning up specific keywords
        page_text = page_text.replace('www', '')
        page_text = page_text.replace('lawcommission', '')
        page_text = page_text.replace('govnp', '')
        page_text = page_text.replace('gov.np', '')
        page_text = page_text.replace('gov np', '')
        page_text = page_text.replace('www.lawcommission.gov.np', '')

        pages.append(page_text.strip())
        doc_lines.append(page_lines)

    end_time = time.time()
    
    title = extract_title(doc_lines[0])
    pdf_data = {
        "title": title,
        "page_count": len(images),
        "filename": filename,
        "ocr_time": f'{end_time - start_time} sec',
        "pages": pages,
        "lines": doc_lines
    }
    
    return pdf_data

def preprocess_all_pdf(pdf_folder_path: str, ocr_json_folder_path: str, ocr_json_batch_size: int):
    pdf_list = glob.glob(f"{pdf_folder_path}/*.pdf")
    pdf_list = sorted(pdf_list)
    json_batch_size = ocr_json_batch_size
    pdf_data_list = []

    os.makedirs(f"{ocr_json_folder_path}/batch", exist_ok=True)
    for i, pdf in enumerate(tqdm(pdf_list, desc="Processing PDFs"), start=1):
        pdf_data = pdf_to_nepali_text(pdf)
        pdf_data_list.append(pdf_data)
        print(pdf_data['title'])
        if i % json_batch_size == 0:
            batch_num = int(i/json_batch_size)
            json_file_path = f"{ocr_json_folder_path}/batch/batch_{batch_num}.json"
            with open(json_file_path, "w") as f:
                    json.dump(pdf_data_list, f, ensure_ascii=False, indent=4)
            pdf_data_list = []

    batch_num += 1 
    json_file_path = f"{ocr_json_folder_path}/batch/batch_{batch_num}.json"
    with open(json_file_path, "w") as f:
            json.dump(pdf_data_list, f, ensure_ascii=False, indent=4)
    pdf_data_list = []  