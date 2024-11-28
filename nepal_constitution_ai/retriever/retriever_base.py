from langchain_core.messages.ai import AIMessage
from loguru import logger
from fastapi import HTTPException
import ast

from nepal_constitution_ai.chat.schemas import ChatResponse, ChatHistory
from nepal_constitution_ai.retriever.chains import (
    RetrieverChain,
    rewrite_query,
    setup_conversation_chain,
)
from nepal_constitution_ai.agent.agent import setup_agent
from nepal_constitution_ai.retriever.utils import get_llm
from nepal_constitution_ai.config.config import settings

class Retriever:
    def __init__(
        self,
        llm: str,
        chat_history: ChatHistory,
        mode: str = "retriever",
    ) -> None:

        self.chat_history = chat_history
        self.llm_model = get_llm(llm)
        self.mode = mode
        self.retriever_chain = RetrieverChain(
            llm_model=self.llm_model,
        ).get_chain()

        self.conv_chain = setup_conversation_chain(
            llm_model=self.llm_model,
        )
        self.agent = setup_agent(
            retriever_chain=self.retriever_chain,
            conv_chain=self.conv_chain,
            llm_model=self.llm_model,
        )

    # invoke function for the retriever
    def invoke(self, query: str):
        try:
            query = query.replace('"', "'")
            
            new_query = rewrite_query(
                query=query, llm_model=self.llm_model, history=self.chat_history
            )

            new_query = new_query.strip()
            new_query = new_query.replace("\n", "")
            if new_query[-2] == ",":
                new_query = new_query[:-2] + "}"

            new_query =  ast.literal_eval(new_query)

            if settings.USE_RERANKING:
                if "categories" in new_query:
                    new_query["categories"] = []
                
            inputs = {
                "user_question": new_query.get("user_question", ""),
                "reformulated_question": new_query.get("reformulated_question", ""),
                "categories": new_query.get("categories", "")
            }
            if self.mode == "evaluation":
                result = self.retriever_chain.invoke(
                    {"input": new_query}
                )
                return result

            result = self.agent.invoke(
                    {"input": inputs, "reformulated_question": new_query.get("reformulated_question", ""), "user_question": new_query.get("user_question", ""), "categories": new_query.get("categories", "")}
                )
            output = result["output"]["answer"]
           
            if isinstance(output, AIMessage):
                if isinstance(output.content, str):
                    output = output.content
                    try:
                        output =  ast.literal_eval(output)
                    except: 
                        output = {"answer": output, "source": "", "link": ""}
                        
                    return ChatResponse(message=output)
                
            return ChatResponse(message={})

        except HTTPException as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            raise HTTPException(
                detail=f"An error occurred while processing your query: {str(e)}",
            )
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return ChatResponse(message={"answer": "Oops! An error occurred while processing your query. Please retry!", "source": "", "link": ""})