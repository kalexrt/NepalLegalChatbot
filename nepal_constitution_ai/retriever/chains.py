from langchain.schema.runnable import RunnableLambda
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate
)
import ast
import json
from langchain_core.runnables import chain
from nepal_constitution_ai.config.config import settings
from langchain_openai import OpenAIEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank
from nepal_constitution_ai.retriever.utils import get_vector_retriever
from nepal_constitution_ai.prompts.prompts import HUMAN_PROMPT, SYSTEM_PROMPT, CONTEXTUALIZE_Q_SYSTEM_PROMPT, CONVERSATION_PROMPT


@chain
def format_docs_with_id(docs):
    """
    Format a list of documents by extracting page content and metadata.
    Each document is formatted with "Content" and "Metadata" sections.
    
    Args:
        docs (list): A list of documents to be formatted.

    Returns:
        str: A string representation of the formatted documents.
    """
    if isinstance(docs, list):
        formatted_output = []

        if not settings.USE_RERANKING:

            # Filter docs by score threshold
            filtered_docs = [(doc, score) for doc, score in docs if score >= settings.RELEVANCE_SCORE_THRESHOLD]

            # Sort filtered docs by relevance score in descending order
            sorted_docs = sorted(filtered_docs, key=lambda x: x[1], reverse=True)

            # Use a dictionary to collect unique documents based on page_content
            unique_docs = {doc.page_content: (doc, score) for doc, score in sorted_docs}.values()

            # Format the output
            for doc, score in unique_docs:
                # Replace specific text in the summary field of metadata
                if 'doc_summary' in doc.metadata:
                    doc.metadata['doc_summary'] = doc.metadata['doc_summary'].replace("The text", "The document from which the above text content is extracted,")
                
                # Append the formatted string
                formatted_output.append(
                    f"Content: {doc.page_content}\nMetadata: {doc.metadata}\nRelevance Score: {score}"
                )
            
            return "\n\n".join(formatted_output)
        
        else:
            for doc in docs:
                # Replace specific text in the summary field of metadata
                if 'doc_summary' in doc.metadata:
                    doc.metadata['doc_summary'] = doc.metadata['doc_summary'].replace("The text", "The document from which the above text content is extracted,")
                
                # Append the formatted string
                formatted_output.append(
                    f"Content: {doc.page_content}\nMetadata: {doc.metadata}"
                )
            return "\n\n".join(formatted_output)

    return "Unexpected document type"

def setup_conversation_chain(llm_model):
    conversation_chain_prompt = ChatPromptTemplate(
        messages=[
            (SystemMessagePromptTemplate.from_template(CONVERSATION_PROMPT)),
        ],
        input_variables=["user_question"],
    )

    return conversation_chain_prompt | llm_model | RunnableLambda(
                lambda x: {
                    "answer": x,
                })

class RetrieverChain:
    """
    A class that integrates a document retriever and an LLM model to retrieve 
    and format documents and generate an answer based on user input.
    """
    def __init__(
        self,
        llm_model
    ) -> None:
        self.llm_model = llm_model


        # Setting the document formatting function
        self.format_docs = format_docs_with_id

        # Defining the prompt template with system and human message templates
        self.prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
                HumanMessagePromptTemplate.from_template(HUMAN_PROMPT),
            ],
            input_variables=["question", "context"],
        )

    def retrieve_and_format(self, inputs):
        """
        Retrieves documents based on the query and formats them.

        Args:
            query (str): The user input query.

        Returns:
            dict: A dictionary containing formatted documents and the original documents.
        """
        if isinstance(inputs, dict):
            docs = self.retriever.invoke(inputs.get("input", ""))
        else:
            inputs = ast.literal_eval(inputs)
            docs = []

            if settings.EMBEDDING_MODEL_PROVIDER == "openai":
                embedding = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL, openai_api_key=settings.OPENAI_API_KEY)
            elif settings.EMBEDDING_MODEL_PROVIDER == "cohere":
                embedding = CohereEmbeddings(model=settings.COHERE_EMBEDDING_MODEL, cohere_api_key=settings.COHERE_API_KEY)
            else:
                embedding = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL, openai_api_key=settings.OPENAI_API_KEY)
           
            if not settings.USE_RERANKING:
                # Query from categories namespaces
                retriever = get_vector_retriever(
                            vector_db="pinecone", embedding=embedding, namespaces=inputs.get("categories", [])
                                )
                for ret in retriever:
                    docs.extend(ret.similarity_search_with_score(query=inputs.get("reformulated_question", ""),k=settings.TOP_K))
            else:
                # Query from default namespace
                default_retriever = get_vector_retriever(
                        vector_db=settings.VECTOR_DB, embedding=embedding, namespaces=None
                            )
                default_retriever = default_retriever[0]
                base_retriever = default_retriever.as_retriever(search_kwargs={"k": settings.TOP_K})

                compressor = CohereRerank(model=settings.COHERE_RERANK_MODEL, cohere_api_key=settings.COHERE_API_KEY)

                compression_retriever = ContextualCompressionRetriever(
                    base_compressor=compressor, 
                    base_retriever=base_retriever  
                )
                compressed_docs = compression_retriever.invoke(inputs.get("reformulated_question", ""))

        formatted_docs = self.format_docs.invoke(compressed_docs)
                

        return {"context": formatted_docs, "question": inputs.get("user_question", ""), "categories": inputs.get("categories", []), "orig_context": docs}

    def generate_answer(self, inputs):
        """
        Generates an answer using the LLM based on the formatted input.

        Args:
            inputs (dict): Contains the formatted documents and the original question.

        Returns:
            dict: Contains the context, generated answer, and original documents.
        """
        formatted_prompt = self.prompt.format(**inputs)
        answer = self.llm_model.invoke(formatted_prompt)

        return {
            "context": inputs.get("context", ""),
            "answer": answer,
            "orig_docs": inputs.get("orig_context", ""),
        }

    def get_chain(self):
        """
        Creates a chain of operations that retrieves, formats, and generates an answer.

        Returns:
            Callable: The chain of operations as a callable object.
        """
        rag_chain = (
            RunnableLambda(self.retrieve_and_format)
            | self.generate_answer
            | RunnableLambda(
                lambda x: {
                    "context": x.get("context", ""),
                    "answer": x.get("answer", ""),
                    "orig_context": x.get("orig_docs", ""),
                }
            )
        )

        return rag_chain


def rewrite_query(query, llm_model, history):
    """
    Reformulates the user's query by incorporating chat history for better context.

    Args:
        query (str): The original user query.
        llm_model (object): The LLM model to generate the reformulated query.
        history (object): The chat history for context.

    Returns:
        str: The reformulated query as text content.
    """

    # Create a prompt to reformulate the query using the chat history
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
            MessagesPlaceholder("doc_categories"),
            (
                "human",
                "{user_question}",
            ),
        ]
    )
    if not settings.USE_RERANKING:
        with open("data/namespace_desc.json", "r") as f:
            doc_categories_desc = json.load(f)
    else:
        doc_categories_desc = []
        
    new_query_chain = contextualize_q_prompt | llm_model
    # Invoke the LLM with the user question and chat history
    res = new_query_chain.invoke(
        {"user_question": query, "doc_categories": [f"Document Categories: {str(doc_categories_desc)}"]}
    )

    return res.content