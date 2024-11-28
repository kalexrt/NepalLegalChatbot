from fastapi import APIRouter

from nepal_constitution_ai.chat.routes import router as chat_routes


router = APIRouter()

router.include_router(chat_routes)

