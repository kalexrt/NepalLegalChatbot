from datetime import datetime
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import JSON

from nepal_constitution_ai.chat.model import ChatSessionModel, ChatMessageModel

async def create_chat_session( db: Session, created_by: UUID):
    """ Create a new chat session in the database. """
    new_chat_session = ChatSessionModel(created_by=created_by, chat_date=datetime.now())
    db.add(new_chat_session)
    db.commit()
    db.refresh(new_chat_session)

    return new_chat_session

def create_chat_message(db: Session, content: str, chat_session_id: UUID, message_by: str):
    """ Create a new chat message in the database. """
    chat_session = get_chat_session_by_id(session_id=chat_session_id, db=db)

    if chat_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    new_message = ChatMessageModel(content=content, chat_session_id=chat_session_id, message_by=message_by, message_time=datetime.now())
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return new_message

async def get_chat_session(user_id: UUID, db: Session):
    session_data = db.query(ChatSessionModel).filter(ChatSessionModel.created_by == user_id).all()

    return session_data

async def update_chat_session(session_id: UUID, user_id: UUID, db: Session):
    session = db.query(ChatSessionModel).filter(ChatSessionModel.chat_session_id == session_id, ChatSessionModel.created_by == user_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    db.commit()
    db.refresh(session)

    return session

def get_data_by_session_id(session_id: UUID, db: Session):
    chat_history = db.query(ChatSessionModel).filter(ChatSessionModel.chat_session_id == session_id).order_by(ChatMessageModel.message_time.asc()).first()

    return chat_history

def get_chat_session_by_id(session_id: UUID, db: Session):
    chat_session = db.query(ChatSessionModel).get(session_id)

    return chat_session


def get_chat_history_service(session_id: UUID, db: Session, fetch_all:bool = False):
    if fetch_all:
        chat_history = db.query(ChatMessageModel).filter(ChatMessageModel.chat_session_id == session_id).order_by(ChatMessageModel.message_time.asc()).all()
    else:
        # chat_history = db.query(ChatMessageModel).filter(ChatMessageModel.chat_session_id == session_id).order_by(ChatMessageModel.message_time.desc()).limit(3)[::-1]
        chat_history = []

    return chat_history
