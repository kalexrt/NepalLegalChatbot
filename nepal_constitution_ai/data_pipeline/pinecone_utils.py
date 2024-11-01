from pinecone import Pinecone, ServerlessSpec
from loguru import logger
import time
from nepal_constitution_ai.config.config import settings

def initialize_pinecone() -> Pinecone:
    logger.info("Initializing Pinecone...")

    pc = Pinecone(
    api_key=settings.PINECONE_API_KEY,
    )

    logger.info("Pinecone initialized successfully.")

    return pc # Returns initialized Pinecone instance

def create_index(pc: Pinecone) -> None:
    logger.info(f"Creating index {settings.PINECONE_INDEX}...")

    if settings.PINECONE_INDEX not in pc.list_indexes().names():
        pc.create_index(
            name=settings.PINECONE_INDEX , 
            dimension=int(settings.EMBEDDING_DIM), 
            spec=ServerlessSpec(
                cloud=settings.PINECONE_CLOUD,
                region=settings.PINECONE_REGION,
            )
        )
    else:
        logger.info(f"Index {settings.PINECONE_INDEX} already exists.")
        

def wait_for_index(pc: Pinecone) -> None:
    logger.info(f"Waiting for index {settings.PINECONE_INDEX} to be ready...")

    # Loop until Pinecone server has started and ready for operations
    while not pc.describe_index(settings.PINECONE_INDEX ).status['ready']:
        time.sleep(1)

    logger.info(f"Index {settings.PINECONE_INDEX} is ready.")

def upsert_vectors(pc: Pinecone, namespace:str, vectors: list[dict]) -> None:
    """Upserts (inserts or updates) vectors into the Pinecone index."""
    index = pc.Index(settings.PINECONE_INDEX)

    logger.info(f"Upserting {len(vectors)} vectors into Pinecone index {settings.PINECONE_INDEX}...")

    index.upsert(vectors=vectors, namespace=namespace) # Main vector upsertion operation

    logger.info(f"Upserted {len(vectors)} vectors into Pinecone index {settings.PINECONE_INDEX}.")

