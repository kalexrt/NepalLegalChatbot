import json
import os
from transformers import MBartForConditionalGeneration, MBart50Tokenizer
from tqdm import tqdm
import torch

def translate_text(text, tokenizer, model):
    """Translate Nepali text to English using mBART model."""
    device="cuda:0" if torch.cuda.is_available() else "cpu"
    try:
        inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True).to(device)
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.lang_code_to_id["en_XX"],
            max_length=1024
        )
        return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def process_batch_file(file_path, tokenizer, model):
    """Process a single batch JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process each document in the batch
        for doc in tqdm(data, desc=f"Processing {os.path.basename(file_path)}"):
            # Translate the pages content
            if 'pages' in doc:
                translated_pages = []
                for page in doc['pages']:
                    page_array = page.split('|')
                    trans_page = ''
                    for sentence in page_array:
                        if len(sentence) > 0:
                            translated_text = translate_text(sentence, tokenizer, model)
                            trans_page += translated_text + ' '
                    translated_pages.append(trans_page)
                doc['pages'] = translated_pages
        
        # Save the translated content
        output_path = file_path.replace('.json', '_translated.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return output_path
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def main():
    # Load model and tokenizer
    print("Loading model and tokenizer...")
    model_name = "facebook/mbart-large-50-many-to-many-mmt"
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(device)

    tokenizer = MBart50Tokenizer.from_pretrained(model_name)
    model = MBartForConditionalGeneration.from_pretrained(model_name).to(device)
    tokenizer.src_lang = "ne_NP"
    

    # Process all batch files in the directory
    batch_dir = "data/ocr_json/batch_v2"                                     
    if not os.path.exists(batch_dir):
        print(f"Directory {batch_dir} not found!")
        return
    
    # Create output directory if it doesn't exist      
    output_dir = os.path.join(batch_dir, "translated")
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each batch file
    batch_files = [f for f in os.listdir(batch_dir) if f.startswith('batch_') and f.endswith('.json')]
    print(f"Found {len(batch_files)} batch files to process")
    
    for batch_file in sorted(batch_files):
        file_path = os.path.join(batch_dir, batch_file)
        print(f"\nProcessing {batch_file}...")
        output_path = process_batch_file(file_path, tokenizer, model)
        if output_path:
            print(f"Successfully translated and saved to: {output_path}")
        else:
            print(f"Failed to process {batch_file}")

if __name__ == "__main__":
    main()