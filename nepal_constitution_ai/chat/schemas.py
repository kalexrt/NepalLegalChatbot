from datetime import datetime
from typing import List
from pydantic import BaseModel
from langchain.schema import BaseChatMessageHistory, BaseMessage
from pydantic.types import UUID4

class ChatSession(BaseModel):
    chat_session_id: UUID4
    chat_date: datetime
    modified_at: datetime
    created_by: UUID4

class ChatMessage(BaseModel):
    chat_message_id: UUID4
    content: str

class ChatSessionRequest(BaseModel):
    question: str
    answer: str

class ChatResponse(BaseModel):
    message: dict = {}

class RetrieverInput(BaseModel):
    query: str
    chat_session_id: UUID4

class ChatHistoryResponse(BaseModel):
    message: str
    date_time: datetime
    actor: str

class ChatHistory(BaseChatMessageHistory):
    def __init__(self):
        super().__init__()
        self.messages: List[BaseMessage] = []

    def add_message(self, message: BaseMessage) -> None:
        self.messages.append(message)

    def clear(self) -> None:
        self.messages = []

    def get_messages(self) -> List[BaseMessage]:
        return self.messages
