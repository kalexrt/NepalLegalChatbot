from ragas import evaluate
from datasets import Dataset
from nepal_constitution_ai.config.config import settings
from nepal_constitution_ai.retriever.utils import get_llm
from nepal_constitution_ai.chat.schemas import ChatHistory
from nepal_constitution_ai.evaluation.data import eval_data
from nepal_constitution_ai.retriever.retriever_base import Retriever
from ragas.metrics import context_precision, answer_relevancy, faithfulness

def run_eval() -> dict: 
    '''
    This function calls the retriever chain and fetches answers with contexts

    Args:
    None

    Returns:
    result: A dictionary with context precision, faithfulness and answer relevance
    '''
    # Initialize ChatHistory and Retriever
    chat_history = ChatHistory()

    retriever = Retriever(
            llm=settings.OPENAI_MODEL,
            chat_history=chat_history,
            mode="evaluation"
        )

    # Iterate through questions and get responses
    for i, question in enumerate(eval_data["question"]):
        response = retriever.invoke(query = question)
        context = response["context"].split("\n\n")
        answer = response["answer"].content
        eval_data["answer"].append(answer)
        eval_data["contexts"].append(context)

    # Convert eval_data dictionary to Dataset object
    eval_dataset = Dataset.from_dict(eval_data)

    # Evaluate using the provided metrics
    result = evaluate(
        eval_dataset,
        metrics=[context_precision, faithfulness, answer_relevancy],
        llm=get_llm(settings.OPENAI_MODEL)
    )

    return result