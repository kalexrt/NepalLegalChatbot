from pdf2image import convert_from_path
import pytesseract
import time
import glob
import json
import os
import re

def pdf_to_nepali_text(pdf_path):
    images = convert_from_path(pdf_path)
    filename = pdf_path.split("/")[-1]
    doc_lines = []
    raw_text = ""
    pages = []
    doc_title = ""
    start_time = time.time()
    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img, lang="nep+eng")
        text = text.replace('www.lawcommission.gov.np', '')
        raw_text += text
        lines = text.splitlines()
        doc_lines += lines
        if lines[0].strip().startswith('www.'):
            lines.pop(0)
        text = '\n'.join(lines)
        text = re.sub(r'[\n\s]+', '\n', text)
        # First page contains the title of the document
        if i == 0:
            # Loop through lines to find the first non-blank line
            for line in lines:
                if line.strip():  # Check if the line is not blank
                    # Split the line by space and check if it has more than two words
                    if len(line.strip().split()) > 1 and all(len(word) > 2 for word in line.strip().split()):
                        doc_title = line.strip()
                        break

        pages.append(text)
    end_time = time.time()
    pdf_data = {
        "title": doc_title,
        "page_count": len(images),
        "filename": filename,
        "ocr_time": f'{(end_time - start_time):.2f} sec',
        "raw_text": raw_text,
        "lines": doc_lines,
        "pages": pages,
    }
    return pdf_data

def preprocess_all_pdf(pdf_folder_path: str, ocr_json_folder_path: str, ocr_json_batch_size: int):
    pdf_list = glob.glob(f"{pdf_folder_path}/*.pdf")
    pdf_list = sorted(pdf_list)
    json_batch_size = ocr_json_batch_size
    pdf_data_list = []

    os.makedirs(f"{ocr_json_folder_path}/batch", exist_ok=True)
    for i, pdf in enumerate(pdf_list, start=1):
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