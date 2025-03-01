import re
import json
import glob
from tqdm import tqdm
from nepal_constitution_ai.data_pipeline.chunking import chunk_text_and_map_pages
from nepal_constitution_ai.data_pipeline.preprocess_pdf import preprocess_all_pdf
from nepal_constitution_ai.data_pipeline.gen_doc_summary import generate_doc_summary
from nepal_constitution_ai.data_pipeline.filter_existing_laws import filter_existing_laws
from nepal_constitution_ai.data_pipeline.embedding import embed_chunks
from nepal_constitution_ai.data_pipeline.pinecone_utils import initialize_pinecone, create_index, wait_for_index, upsert_vectors
from nepal_constitution_ai.data_pipeline.utils import find_key_by_filename, find_entry_by_filename
from nepal_constitution_ai.config.config import settings

def main():
    """
    Main function to process a PDF file, embed its content, and store it in a Pinecone index.
    
    Returns:
    None
    """
    ## Preprocess all PDFs in the specified directory and store the OCR JSON files
    preprocess_all_pdf(settings.DOWNLOADED_PDF_PATH, settings.OCR_JSON_FOLDER_PATH, settings.OCR_JSON_BATCH_SIZE)

    # Generate document summaries for all OCR JSON files
    if settings.GENERATE_DOC_SUMMARY:
        generate_doc_summary(settings.OCR_JSON_FOLDER_PATH)

    filter_existing_laws(settings.EXISTING_LAWS_JSON_FILE_PATH, f"{settings.OCR_JSON_FOLDER_PATH}/batch", settings.EXISTING_LAWS_FOLDER_PATH)

    # Initialize Pinecone service, create index and wait for pinecone to be ready for upsertion
    pc = initialize_pinecone()
    create_index(pc)
    wait_for_index(pc)

    namespace_mapping_filepath = f"{settings.DATA_PATH}/namespace_mapping.json"
    documents_info_json = f"{settings.DATA_PATH}/documents_info.json"
    existing_laws_json_files = glob.glob(f"{settings.EXISTING_LAWS_FOLDER_PATH}/*.json")
    existing_laws_json_files = sorted(existing_laws_json_files, key=lambda x: int(re.search(r'\d+', x).group()))
    batch_num = 0
    curr_chunk_num = 31045 # index of the chunk in the current batch for default namespace
    namespace_mapping = {}

    with open(documents_info_json, 'r') as file:
            documents_info = json.load(file)

    for json_file in tqdm(existing_laws_json_files, "Embedding chunks and uploading to Vector DB"):
        with open(json_file, 'r') as file:
            docs = json.load(file)
        batch_num += 1
        emb_json_filepath = f"{settings.EMBS_JSON_FOLDER_PATH}/embeddings_batch_{batch_num}.json"
        chunks_json_filepath = f"{settings.CHUNKS_JSON_FOLDER_PATH}/chunks_batch_{batch_num}.json"
        batch_vectors = []
        batch_chunks = []
        for doc in docs:    
            namespace = find_key_by_filename(documents_info, doc['filename'])
            namespace = namespace.replace(" ", "_")
            doc_link = find_entry_by_filename(documents_info, doc['filename'])['nep_pdf_link']

            # Check if the namespace is already in namespace_mapping
            if namespace not in namespace_mapping:
                namespace_mapping[namespace] = []
            # Load and chunk the PDF content into text chunks and their corresponding metadata
            chunks, chunks_dict_with_pagenum = chunk_text_and_map_pages(doc, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            batch_chunks.extend(chunks_dict_with_pagenum)
            
            embedded_chunks = embed_chunks(batch_num ,chunks)
            doc_title = doc['title']
            doc_summary = doc["summary"]
            # Prepare the vectors (wi"th IDs and embedded values) for upsertion into Pinecone
            vectors = [
                {
                    "id": f"chunk_{i+curr_chunk_num+1}", 
                    "values": emb, 
                    "metadata": {"text": chunk['text'], "source": f"Page {chunk['page']} from {doc_title}", "link": doc_link, "doc_summary": doc_summary}
                }
                # Loop through chunks and embeddings to generate vectors list 
                for i, (chunk, emb) in enumerate(zip(chunks_dict_with_pagenum, embedded_chunks))
                ]

            curr_chunk_num += len(vectors)

            if settings.CREATE_NAMESPACE: # If aggregate namespace is available then, individual namespace can be ommitted
                # Upsert (insert or update) the vectors into the respective namespace so that, they can be retrieved from specific namespaces as well
                upsert_vectors(pc, namespace, vectors)
                namespace_mapping[namespace].append(doc_title)
                for vector in vectors:
                    vector["metadata"]["namespace"] = namespace

            # Append vectors to the list of all vectors for creating a aggregate namespace
            batch_vectors.extend(vectors)

        # Store the batch chunks in a JSON file
        with open(chunks_json_filepath, 'w') as json_file:
            json.dump(batch_chunks, json_file, ensure_ascii=False, indent=4)

        # Store the batch embedding vectors in a JSON file
        with open(emb_json_filepath, 'w') as json_file:
            json.dump(batch_vectors, json_file, ensure_ascii=False, indent=4)

        if settings.CREATE_NAMESPACE:
            with open(namespace_mapping_filepath, 'w') as json_file:
                json.dump(namespace_mapping, json_file, ensure_ascii=False, indent=4)
            continue

        # Upsert (insert or update) the vectors into the default namespace
        upsert_vectors(pc, None, batch_vectors)

if __name__ == "__main__":
    main()  
