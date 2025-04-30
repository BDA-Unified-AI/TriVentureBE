from fastapi import APIRouter, status, Depends
from typing import Annotated, Optional
from fastapi.responses import JSONResponse
from pydantic import Field
from src.apis.models.user_models import User
from src.apis.models.BaseModel import BaseDocument
from src.apis.middlewares.auth_middleware import get_current_user
from src.apis.controllers.comment_controller import (
    create_a_comment_controller,
    get_comments_of_a_post_controller,
    update_a_comment_controller,
    delete_a_comment_controller,
)
from src.utils.redis import set_key_redis, get_key_redis
from src.utils.logger import logger

router = APIRouter(prefix="/comment", tags=["Comment"])

user_dependency = Annotated[User, Depends(get_current_user)]


class BodyComment(BaseDocument):
    content: str = Field("", description="Comment's content")
    post_id: str = Field("", description="Post's id")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "John Doe",
                "post_id": "1234567890",
            }
        }


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_comment(body: BodyComment, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]
    result = await create_a_comment_controller(
        body.content,
        user_id,
        body.post_id,
    )
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=201)


@router.get("/get/{post_id}", status_code=status.HTTP_200_OK)
async def get_comments_of_a_post(post_id: str):
    result = await get_comments_of_a_post_controller(post_id)
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)


class BodyUpdateComment(BaseDocument):
    comment_id: str = Field("", description="Comment's id")
    content: Optional[str] = Field("", description="Comment's content")

    class Config:
        json_schema_extra = {
            "example": {
                "comment_id": "1234567890",
                "content": "John Doe",
            }
        }


@router.patch("/update/", status_code=status.HTTP_200_OK)
async def update_comment(body: BodyUpdateComment, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    result = await update_a_comment_controller(
        user["id"],
        body.comment_id,
        body.content,
    )
    logger.info(f"RESULT: {result}")
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)


@router.delete("/delete/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_comment(comment_id: str, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    result = await delete_a_comment_controller(user["id"], comment_id)
    logger.info(f"RESULT: {result}")
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)
