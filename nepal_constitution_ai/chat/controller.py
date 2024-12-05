from uuid import UUID

from fastapi import BackgroundTasks
from langchain.schema import AIMessage, HumanMessage
from pydantic.types import UUID4
from sqlalchemy.orm import Session

from nepal_constitution_ai.chat import schemas
from nepal_constitution_ai.chat.schemas import ChatHistory
from nepal_constitution_ai.retriever.retriever_base import Retriever
from nepal_constitution_ai.user.model import User
from nepal_constitution_ai.config.config import settings
import nepal_constitution_ai.chat.services as chat_service


async def create_chat_session(db: Session, created_by: UUID4):
    new_chat_session = await chat_service.create_chat_session(
        db=db,
        created_by=created_by,
    )

    return new_chat_session


async def update_chat_session(user_id: UUID, session_id: UUID, request: schemas.ChatSessionRequest, db: Session):
    updated_session = await chat_service.update_chat_session(
        user_id=user_id, session_id=session_id, db=db
    )

    return updated_session


async def get_chat_session(user_id: UUID, db: Session):
    session = await chat_service.get_chat_session(user_id=user_id, db=db)

    return session





def get_chat_history_by_session_id(session_id: UUID, db: Session):
    chat_messages = chat_service.get_chat_history_service(db=db, session_id=session_id)
    res = []

    for chat_message in chat_messages:

        answer = chat_message.content
        response = schemas.ChatHistoryResponse(
            message=answer,
            actor=chat_message.message_by,
            date_time=chat_message.message_time,
        )
        res.append(response)

    return res

def user_input(db: Session, user: User, query: str, chat_session_id: UUID):
    background_tasks = BackgroundTasks()

    background_tasks.add_task(
        chat_service.create_chat_message(
            db=db,
            content=query,
            chat_session_id=chat_session_id,
            message_by="user",
        )
    )

    message_history = get_chat_history_by_session_id(session_id=chat_session_id, db=db)

    chat_history = ChatHistory()
    for chat_message in message_history:
        if chat_message.actor == "user":
            chat_history.add_message(HumanMessage(content=chat_message.message))
        elif chat_message.actor == "llm":
            chat_history.add_message(AIMessage(content=chat_message.message))

    retriever = Retriever(
        llm=settings.OPENAI_MODEL,
        chat_history=chat_history,
    )
    response = retriever.invoke(query=query)
    response = response.message

    background_tasks.add_task(
        chat_service.create_chat_message(
            db=db,
            content=str(response),
            chat_session_id=chat_session_id,
            message_by="llm",
        )
    )

    if response.get("source", "") == "" and response.get("link", "") == "":
        formatted_response = response.get("answer", "")
    else:
        try:
            link_title = response.get('source', "").split("from", 1)[1].strip()
        except:
            link_title = "Click Here"

        formatted_response = f"""
        {response.get('answer', "")}

        **Source:** {response.get('source', "")}

        **Link:** [{link_title}]({response.get('link', "")})
        """

    return formatted_response