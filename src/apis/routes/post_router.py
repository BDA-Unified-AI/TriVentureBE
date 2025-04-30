from fastapi import APIRouter, status, Depends, BackgroundTasks, Query
from typing import Annotated, Optional
from fastapi.responses import JSONResponse
from pydantic import Field
from src.apis.models.user_models import User
from src.apis.models.BaseModel import BaseDocument
from src.apis.middlewares.auth_middleware import get_current_user
from src.apis.controllers.post_controller import (
    create_a_post_controller,
    list_all_posts_controller,
    list_posts_by_destination_controller,
    get_a_post_controller,
    update_a_post_controller,
    delete_a_post_controller,
)
from src.utils.redis import set_key_redis, get_key_redis
from src.utils.logger import logger

router = APIRouter(prefix="/post", tags=["Post"])

user_dependency = Annotated[User, Depends(get_current_user)]


class BodyPost(BaseDocument):
    content: str = Field("", description="Post's content")
    destination_id: str = Field(..., description="Destination's id", min_length=1)
    images_base64: Optional[list] = Field([], description="Images base64")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "John Doe",
                "destination_id": "1234567890",
                "images_base64": ["base64_image1", "base64_image2"],
            }
        }
    }


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_post(body: BodyPost, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]
    result = await create_a_post_controller(
        body.content,
        user_id,
        body.destination_id,
        body.images_base64,
    )
    logger.info(f"RESULT: {result}")
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=201)


@router.get("/get/{post_id}", status_code=status.HTTP_200_OK)
async def get_post(post_id: str):
    result = await get_a_post_controller(post_id)
    logger.info(f"RESULT: {result}")
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)


@router.get("/list", status_code=status.HTTP_200_OK)
async def list_all_posts(user_id: Optional[str] = None, page: int = Query(default=1, ge=1)):
    # result = await get_key_redis("all_posts")
    result = None
    # result = eval(result) if result else None
    if not result:
        result = await list_all_posts_controller(user_id, page)
        print("result", result)
        # background_tasks.add_task(set_key_redis, "all_posts", str(result), 20)
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)


@router.get("/list_post_destination", status_code=status.HTTP_200_OK)
async def list_all_posts_destination(
    destination_id: str,
    user_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
):
    # result = await get_key_redis("all_posts")
    result = None
    result = eval(result) if result else None
    if not result:
        result = await list_posts_by_destination_controller(destination_id, user_id, page)
        # background_tasks.add_task(set_key_redis, "all_posts", str(result),20)
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)


class BodyUpdatePost(BaseDocument):
    content: str = Field(..., description="Post's content", min_length=1)
    post_id: str = Field(..., description="Post's id", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "content": "John Doe",
                "post_id": "1234567890",
            }
        }


@router.patch("/update/", status_code=status.HTTP_200_OK)
async def update_post(body: BodyUpdatePost, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    result = await update_a_post_controller(
        user["id"],
        body.post_id,
        body.content,
    )
    logger.info(f"RESULT: {result}")
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)


@router.delete("/delete/{post_id}", status_code=status.HTTP_200_OK)
async def delete_post(post_id: str, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    result = await delete_a_post_controller(user["id"], post_id)
    logger.info(f"RESULT: {result}")
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)
