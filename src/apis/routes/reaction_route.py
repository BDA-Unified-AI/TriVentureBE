from fastapi import APIRouter, status, Depends
from typing import Annotated, Optional
from fastapi.responses import JSONResponse
from pydantic import Field
from src.apis.models.user_models import User
from src.apis.models.BaseModel import BaseDocument
from src.apis.middlewares.auth_middleware import get_current_user
from src.apis.controllers.reaction_controller import (
    create_a_reaction_controller,
    list_all_reaction_controller,
    update_a_reaction_controller,
    delete_a_reaction_controller,
)
from src.utils.mongo import ReactionCRUD, PostCRUD
from src.utils.redis import set_key_redis, get_key_redis
from src.utils.logger import logger
from bson import ObjectId

router = APIRouter(prefix="/reaction", tags=["Reaction"])

user_dependency = Annotated[User, Depends(get_current_user)]


class BodyLike(BaseDocument):
    post_id: str = Field("", description="Post's id", min_length=1)
    type: int = Field(0, description="Type of like", ge=0, lt=5)

    class Config:
        json_schema_extra = {
            "example": {
                "post_id": "123213213",
                "type": 1,
            }
        }


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_reaction(body: BodyLike, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]
    result = await create_a_reaction_controller(
        user_id,
        body.post_id,
        body.type,
    )
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=201)


@router.get("/get/{post_id}", status_code=status.HTTP_200_OK)
async def get_reactions_of_a_post(post_id: str):
    result = await list_all_reaction_controller(post_id)
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)


class BodyUpdateReaction(BaseDocument):
    reaction_id: str = Field("", description="Reaction's id")
    type: str = Field("", description="Type of like", gt=0, lt=5)

    class Config:
        json_schema_extra = {
            "example": {
                "reaction_id": "1234567890",
                "type": 1,
            }
        }


class BodyUpdateReactionInteract(BaseDocument):
    reaction_id: Optional[str] = Field("", description="Reaction's id")
    post_id: str = Field("", description="Post's id", min_length=1)
    current_type: int = Field("", description="Current type of like", ge=0, lt=5)
    type: int = Field(0, description="Type of like", ge=0, lt=5)
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reaction_id": "1234567890",
                    "post_id": "1234567890",
                    "current_type": 1,
                    "type": 2,
                },
            ]
        }
    }


@router.post("/interact/", status_code=status.HTTP_200_OK)
async def interact_reaction(body: BodyUpdateReactionInteract, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    if not body.reaction_id:
        response = await ReactionCRUD.create(
            {"user_id": user["id"], "post_id": body.post_id, "type": body.type}
        )
        await PostCRUD.update(
            {"_id": ObjectId(body.post_id)}, {"$inc": {"reaction_count": 1}}
        )

        return JSONResponse(content={"reaction_id": str(response)}, status_code=201)
    elif body.current_type == body.type:
        await ReactionCRUD.delete_one({"_id": ObjectId(body.reaction_id)})
        await PostCRUD.update(
            {"_id": ObjectId(body.post_id)}, {"$inc": {"reaction_count": -1}}
        )
        return JSONResponse(content={"message": "Reaction deleted"}, status_code=200)
    elif body.current_type != body.type:
        await ReactionCRUD.update(
            {"_id": ObjectId(body.reaction_id)}, {"$set": {"type": body.type}}
        )
        return JSONResponse(content={"message": "Reaction updated"}, status_code=200)

    return JSONResponse(content={"message": "Reaction not found"}, status_code=404)


@router.patch("/update/", status_code=status.HTTP_200_OK)
async def update_reaction(body: BodyUpdateReaction, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    result = await update_a_reaction_controller(
        user["id"],
        body.reaction_id,
        body.type,
    )
    logger.info(f"RESULT: {result}")
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)


@router.delete("/delete/{reaction_id}", status_code=status.HTTP_200_OK)
async def delete_reaction(reaction_id: str, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    result = await delete_a_reaction_controller(user["id"], reaction_id)
    logger.info(f"RESULT: {result}")
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)
