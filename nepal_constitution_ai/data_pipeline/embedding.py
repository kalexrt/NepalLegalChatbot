from langchain_openai import OpenAIEmbeddings
from langchain_cohere import CohereEmbeddings
from loguru import logger
from nepal_constitution_ai.config.config import settings
import time


def embed_chunks(batch, chunked_data: list[str]) -> list[list[float]]:
    """Embeds a list of text chunks into vector representations using the OpenAI embeddings model.
    Returns the embedded vectors or None if an error occurs.
    """
    try:
        logger.info("Embedding chunks...")
        if settings.EMBEDDING_MODEL_PROVIDER == "openai":
            logger.info("Using OpenAI embeddings model: {}".format(settings.OPENAI_EMBEDDING_MODEL))
            model = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL, openai_api_key=settings.OPENAI_API_KEY)
        elif settings.EMBEDDING_MODEL_PROVIDER == "cohere":
            logger.info("Using Cohere embeddings model: {}".format(settings.COHERE_EMBEDDING_MODEL))
            model = CohereEmbeddings(model=settings.COHERE_EMBEDDING_MODEL, cohere_api_key=settings.COHERE_API_KEY)
        else:
            logger.info("Using OpenAI embeddings model (DEFAULT): {}".format(settings.OPENAI_EMBEDDING_MODEL))
            model = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL, openai_api_key=settings.OPENAI_API_KEY)            

        api_key = "JNIHCGPTq3kyItMXwe83019Ckjn9CxTrUHtSfulS"



        model = CohereEmbeddings(model=settings.COHERE_EMBEDDING_MODEL, cohere_api_key=api_key)
        embs = []        
        for i in range(0, len(chunked_data), 50):
            batch = chunked_data[i:i + settings.VECTORS_UPLOAD_BATCH_SIZE]  # Slice the list into batches

            try:
                embedded_chunks = model.embed_documents(batch)
                logger.info("Chunks embedded successfully.")
                embs.extend(embedded_chunks)
            except:
                logger.info("Wait for 80 sec")
                time.sleep(80)
                embedded_chunks = model.embed_documents(batch)
                embs.extend(embedded_chunks)

                logger.info("Chunks embedded successfully after delay.")

        return embs
    
    except Exception as e:  # Catch any exception during the embedding process and return none
        logger.error(f"An error occurred while embedding chunks: {e}")  
        raise e
