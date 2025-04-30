from fastapi import APIRouter, status, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Annotated
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from src.apis.interfaces.api_interface import Chat
from src.apis.controllers.chat_controller import (
    chat_function,
    chat_streaming_function,
    get_history_function,
    list_chat_history_function,
    delete_chat_history_function,
    chat_streaming_no_login_function,
)
from src.utils.logger import logger
from src.apis.models.user_models import User
from src.apis.middlewares.auth_middleware import get_current_user
from src.utils.redis import set_key_redis, delete_key_redis

load_dotenv(override=True)

router = APIRouter(prefix="/llm", tags=["LLM"])

user_dependency = Annotated[User, Depends(get_current_user)]


@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat_router(
    data: Chat, user: user_dependency, background_tasks: BackgroundTasks
):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    return await chat_function(user, data, background_tasks)


@router.post("/chat_streaming", status_code=status.HTTP_200_OK)
async def chat_streaming_router(
    data: Chat, user: user_dependency, background_tasks: BackgroundTasks
):
    return StreamingResponse(
        chat_streaming_function(user, data, background_tasks),
        media_type="text/plain",
    )

@router.post("/chat_streaming_guest", status_code=status.HTTP_200_OK)
async def chat_streaming_guest_router(
    data: Chat, background_tasks: BackgroundTasks
):
    return StreamingResponse(
        chat_streaming_no_login_function(data, background_tasks),
        media_type="text/plain",
    )


@router.post("/get_chat_history", status_code=status.HTTP_200_OK)
async def get_chat_history(user: user_dependency, background_tasks: BackgroundTasks):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]
    result = await get_history_function(user_id, background_tasks)
    if result is None:
        return JSONResponse(content={"message": [], "intent": None}, status_code=500)
    background_tasks.add_task(set_key_redis, f"chat_history_{user_id}", str(result))
    return JSONResponse(content=result, status_code=200)


@router.delete("/delete_chat_history", status_code=status.HTTP_200_OK)
async def delete_chat_history(user: user_dependency, background_tasks: BackgroundTasks):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    try:
        await delete_chat_history_function(user["id"])
        background_tasks.add_task(delete_key_redis, f"chat_history_{user['id']}")

    except Exception as e:
        logger.error(f"Error in delete_chat_history: {e}")

    return JSONResponse(
        content={"message": "Chat history has been deleted"}, status_code=200
    )


@router.get("/list_chat_history", status_code=status.HTTP_200_OK)
async def list_chat_history(user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    try:
        result = await list_chat_history_function(user["id"])
        await set_key_redis(f"list_chat_history_{user['id']}", str(result))
    except Exception as e:
        logger.error(f"Error in list_chat_history: {e}")
        result = []

    return JSONResponse(content=result, status_code=200)
