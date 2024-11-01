from nepal_constitution_ai.data_pipeline.chunking import load_and_chunk_pdf_content
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

    # Load and chunk the PDF content into text chunks and their corresponding metadata
    chunked_data_dict_list, chunked_data = load_and_chunk_pdf_content(settings.FILE_PATH)
    embedded_chunks = embed_chunks(chunked_data)

    # Initialize Pinecone service, create index and wait for pinecone to be ready for upsertion
    pc = initialize_pinecone()
    create_index(pc)
    wait_for_index(pc)
    
    # Prepare the vectors (with IDs and embedded values) for upsertion into Pinecone
    vectors = [
        {
            "id": f"chunk_{i+1}", 
            "values": emb, 
            "metadata": [{"text": chunk[key], "source": key} for key in chunk][-1]
        }
        # Loop through chunks and embeddings to generate vectors list 
        for i, (chunk, emb) in enumerate(zip(chunked_data_dict_list, embedded_chunks))
        ]
    
    # Define the namespace for the vectors
    namespace = "nepal_constitution_ai"

    # Upsert (insert or update) the vectors into the Pinecone index
    upsert_vectors(pc, namespace, vectors)

if __name__ == "__main__":
    main()
