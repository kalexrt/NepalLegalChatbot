import re
import json
import glob
from tqdm import tqdm
from nepal_constitution_ai.data_pipeline.chunking import chunk_text_and_map_pages
from nepal_constitution_ai.data_pipeline.preprocess_pdf import preprocess_all_pdf
from nepal_constitution_ai.data_pipeline.embedding import embed_chunks
from nepal_constitution_ai.data_pipeline.pinecone_utils import initialize_pinecone, create_index, wait_for_index, upsert_vectors
from nepal_constitution_ai.config.config import settings

def main():
    """
    Main function to process a PDF file, embed its content, and store it in a Pinecone index.
    
    Returns:
    None
    """
    # Preprocess all PDFs in the specified directory and store the OCR JSON files
    # preprocess_all_pdf(settings.DOWNLOADED_PDF_PATH, settings.OCR_JSON_FOLDER_PATH, settings.OCR_JSON_BATCH_SIZE)

    # Initialize Pinecone service, create index and wait for pinecone to be ready for upsertion
    pc = initialize_pinecone()
    create_index(pc)
    wait_for_index(pc)

    namespace_mapping_filepath = f"{settings.OCR_JSON_FOLDER_PATH}/namespace_mapping.json"
    ocr_json_files = glob.glob(f"{settings.OCR_JSON_FOLDER_PATH}/batch/*.json")
    ocr_json_files = sorted(ocr_json_files, key=lambda x: int(re.search(r'\d+', x).group()))
    batch_num = 0 # index of doc for namespace in Pinecone
    curr_chunk_num = 0 # index of the chunk in the current batch for default namespace
    namespace_mapping = {}

    for json_file in tqdm(ocr_json_files, "Embedding chunks and uploading to Vector DB"):
        with open(json_file, 'r') as file:
            docs = json.load(file)
        batch_num += 1
        namespace = f"batch-num-{batch_num}"
        namespace_mapping[namespace] = []
        emb_json_filepath = f"{settings.EMBS_JSON_FOLDER_PATH}/embeddings_batch_{batch_num}.json"
        chunks_json_filepath = f"{settings.CHUNKS_JSON_FOLDER_PATH}/chunks_batch_{batch_num}.json"
        batch_vectors = []
        batch_chunks = []
        for doc in docs:    
            # Load and chunk the PDF content into text chunks and their corresponding metadata
            chunks, chunks_dict_with_pagenum = chunk_text_and_map_pages(doc['pages'], settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            batch_chunks.extend(chunks_dict_with_pagenum)

            embedded_chunks = embed_chunks(chunks)
            doc_title = doc['title']
            # Prepare the vectors (wi"th IDs and embedded values) for upsertion into Pinecone
            vectors = [
                {
                    "id": f"chunk_{i+1}", 
                    "values": emb, 
                    "metadata": {"text": chunk['text'], "source": f"Page {chunk['page']} from {doc_title}"}
                }
                # Loop through chunks and embeddings to generate vectors list 
                for i, (chunk, emb) in enumerate(zip(chunks_dict_with_pagenum, embedded_chunks))
                ]
            # Append vectors to the list of all vectors for creating a aggregate namespace
            batch_vectors.extend(vectors)

            if settings.CREATE_NAMESPACE: # If aggregate namespace is available then, individual namespace can be ommitted
                # Upsert (insert or update) the vectors into the respective namespace so that, they can be retrieved from specific namespaces as well
                upsert_vectors(pc, namespace, vectors)
                namespace_mapping[namespace].append(doc_title)

        if settings.CREATE_NAMESPACE:
            with open(namespace_mapping_filepath, 'w') as json_file:
                json.dump(namespace_mapping, json_file, ensure_ascii=False, indent=4)
            continue

        # Store the batch embedding vectors in a JSON file
        with open(emb_json_filepath, 'w') as json_file:
            for i in range(len(batch_vectors)):
                batch_vectors[i]['id'] = f"chunk_{i+curr_chunk_num+1}"
            json.dump(batch_vectors, json_file, ensure_ascii=False, indent=4)
            curr_chunk_num += len(batch_vectors)

        # Store the batch embedding vectors in a JSON file
        with open(chunks_json_filepath, 'w') as json_file:
            json.dump(batch_chunks, json_file, ensure_ascii=False, indent=4)

        # Upsert (insert or update) the vectors into the default namespace
        upsert_vectors(pc, None, batch_vectors)

if __name__ == "__main__":
    main()
