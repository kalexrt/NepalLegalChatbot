import re
import json
import glob  
from tqdm import tqdm
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from nepal_constitution_ai.retriever.utils import get_llm
from nepal_constitution_ai.prompts.prompts import SUMMARIZE_DOCUMENT_PROMPT

def generate_doc_summary(ocr_json_folder_path):
    """
    Generate document summaries for all OCR JSON files in the specified folder.
    """
    # Define the number of pages to consider for generating a summary
    NUM_PAGES_TO_GENERATE_SUMMARY = 2


    summarize_doc_prompt = ChatPromptTemplate.from_template(SUMMARIZE_DOCUMENT_PROMPT)
    llm = get_llm("gpt-3.5-turbo")
     # Create a chain with the LLM and prompt
    summary_chain =summarize_doc_prompt | llm | StrOutputParser()

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

            # Extract text from the selected pages
            combined_text = ' '.join(beginning_pages)
            
            # Generate summary using langchain
            try:
                response = summary_chain.invoke(input=combined_text)

                # Store the summary
                doc['summary'] = response.strip()
            
            except Exception as e:
                print(f"Error generating summary for document: {e}")
                raise e
        
        # Save the updated batch JSON file with summaries
        with open(json_file, 'w') as json_file:
            json.dump(docs, json_file, ensure_ascii=False, indent=4)