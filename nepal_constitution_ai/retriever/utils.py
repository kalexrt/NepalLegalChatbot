from loguru import logger
from langchain_pinecone import PineconeVectorStore
from langchain_core.messages.ai import AIMessage

from nepal_constitution_ai.models.openai.openai_model import OpenaiModel
from nepal_constitution_ai.config.config import settings

def get_llm(llm_name: str) -> OpenaiModel:
    """
    Retrieves an OpenAI model based on the given model name. The function checks
    if the provided LLM name matches one of the predefined models (GPT-3.5, GPT-4).

    Args:
        llm_name (str): The name of the desired LLM model.

    Returns:
        OpenaiModel: The selected OpenAI model.

    Raises:
        ValueError: If the provided LLM name is invalid.
    """
    try:
        llm_model = OpenaiModel(llm_name).model_selection()
    except ValueError:
        logger.error(f"Invalid LLM model selected: {llm_name}")
        raise ValueError("Wrong llm model selected")
    except Exception as e:
        logger.error(f"An error occurred while retrieving the llm model: {e}")
        raise e

    logger.info(f"Successfully retrieved model: {llm_name}")
    return llm_model


def get_vector_retriever(vector_db: str, embedding, namespaces=None):
    """
    Retrieves a vector store retriever based on the given vector database name.
    Specifically configured for Pinecone, the function returns a retriever that
    can perform similarity search with the specified number of top results (k).

    Args:
        vector_db (str): The name of the vector database (e.g., 'pinecone').
        embedding (callable): The embedding function used to convert queries into vectors.
        k (int, optional): The number of top similar results to return.

    Returns:
        PineconeVectorStore: A configured Pinecone retriever object.

    Raises:
        ValueError: If an unsupported vector database is provided.
    """
    try:
        pinecone_index = settings.PINECONE_INDEX
        retriever = []

        if namespaces:
            for namespace in namespaces:
                retriever.append(PineconeVectorStore(
                        index_name=pinecone_index,
                        embedding=embedding,
                        pinecone_api_key=settings.PINECONE_API_KEY,
                        namespace=namespace
                    ))
        else:
            retriever.append(PineconeVectorStore(
                    index_name=pinecone_index,
                    embedding=embedding,
                    pinecone_api_key=settings.PINECONE_API_KEY,
                ))

        logger.info(f"Successfully created retriever for vector database: {vector_db}")
        return retriever

    except ValueError:
        logger.error(f"Unsupported vector database provided: {vector_db}")
        raise ValueError(f"Unsupported vector database: {vector_db}")
    except Exception as e:
        logger.error(f"An error occurred while retrieving the vector retriever: {e}")
        raise e
    
def format_chat_history(chat_history: list) -> str:
    """
    Formats the chat history into a dictionary format.
    """
    chat_history_formatted = ""
    for message in chat_history:
        if isinstance(message, AIMessage):
            chat_history_formatted += f"\nAI: {message.content}\n"
        else:
            chat_history_formatted += f"\nUser: {message.content}"

    return chat_history_formatted