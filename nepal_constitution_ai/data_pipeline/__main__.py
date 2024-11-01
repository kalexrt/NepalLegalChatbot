import json
import glob
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
    preprocess_all_pdf(settings.DOWNLOADED_PDF_PATH, settings.OCR_JSON_FOLDER_PATH, settings.OCR_JSON_BATCH_SIZE)

    # Initialize Pinecone service, create index and wait for pinecone to be ready for upsertion
    pc = initialize_pinecone()
    create_index(pc)
    wait_for_index(pc)

    ocr_json_files = glob.glob(f"{settings.OCR_JSON_FOLDER_PATH}/*.json")
    doc_num = 0 # index of doc for namespace in Pinecone
    for json_file in ocr_json_files:
        with open(json_file, 'r') as file:
            docs = json.load(file)
        for doc in docs:    
            # Load and chunk the PDF content into text chunks and their corresponding metadata
            chunks, chunks_dict_with_pagenum = chunk_text_and_map_pages(doc['pages'], settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            embedded_chunks = embed_chunks(chunks)
            doc_title = doc['title']
            doc_num += 1
            namespace = f"doc-num-{doc_num}"
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
            # Upsert (insert or update) the vectors into the Pinecone index
            upsert_vectors(pc, namespace, vectors)

if __name__ == "__main__":
    main()
