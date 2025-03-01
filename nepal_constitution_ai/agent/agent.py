from nepal_constitution_ai.agent.utils import create_agent
from nepal_constitution_ai.retriever.chains import RetrieverChain
from nepal_constitution_ai.models.openai.openai_model import OpenaiModel
from langchain.chains import LLMChain
from typing import Union
import ast
from langchain.tools import Tool

def setup_agent(
    retriever_chain: RetrieverChain,
    conv_chain: LLMChain,
    llm_model: Union[OpenaiModel],
):
    tools = [
        Tool(
            name="Vector Search",
            func=lambda query: retriever_chain.invoke(query),
            description=f"Useful for answering any legal questions related to nepal laws, constitution, rules and regulations etc.",
            return_direct=True,
        ),
        Tool(
            name="Conversation",
            func=lambda query: conv_chain.invoke(ast.literal_eval(query)),
            description="Useful for greetings, general conversation",
            return_direct=True,
        ),
    ]

    return create_agent(
        llm_model,
        tools
    )