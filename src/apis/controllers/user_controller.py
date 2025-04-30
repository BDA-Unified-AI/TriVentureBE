from datetime import datetime
from src.utils.mongo import UserCRUD
from src.utils.logger import logger
from bson import ObjectId
from fastapi.responses import JSONResponse
from typing import Dict


async def list_users_controller():
    try:
        users = await UserCRUD.find_all()
        # Convert datetime fields to ISO format
        for user in users:
            if "created_at" in user and isinstance(user["created_at"], datetime):
                user["created_at"] = user["created_at"].isoformat()
            if "updated_at" in user and isinstance(user["updated_at"], datetime):
                user["updated_at"] = user["updated_at"].isoformat()
            if "expire_at" in user and isinstance(user["expire_at"], datetime):
                user["expire_at"] = user["expire_at"].isoformat()
        return JSONResponse(
            content={
                "status": "success",
                "data": users,
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e),
            },
            status_code=500,
        )


async def update_user_controller(user_id: str, user_data: dict):
    try:
        user = await UserCRUD.update({"_id": ObjectId(user_id)}, user_data)

        # Convert datetime fields to ISO format
        if user:
            if "created_at" in user and isinstance(user["created_at"], datetime):
                user["created_at"] = user["created_at"].isoformat()
            if "updated_at" in user and isinstance(user["updated_at"], datetime):
                user["updated_at"] = user["updated_at"].isoformat()
            if "expire_at" in user and isinstance(user["expire_at"], datetime):
                user["expire_at"] = user["expire_at"].isoformat()

            return JSONResponse(
                content={
                    "status": "success",
                    "data": user,
                },
                status_code=200,
            )
        else:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "User not found",
                },
                status_code=404,
            )
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e),
            },
            status_code=500,
        )


async def delete_user_controller(user_id: str):
    try:
        user = await UserCRUD.delete_one({"_id": ObjectId(user_id)})
        return JSONResponse(
            content={
                "status": "success",
                "data": user,
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e),
            },
            status_code=500,
        )


async def get_user_by_id_controller(user_id: str):
    try:
        user = await UserCRUD.find_by_id(user_id)
        if not user:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "User not found",
                },
                status_code=404,
            )
        # Convert datetime fields to ISO format
        if "created_at" in user and isinstance(user["created_at"], datetime):
            user["created_at"] = user["created_at"].isoformat()
        if "updated_at" in user and isinstance(user["updated_at"], datetime):
            user["updated_at"] = user["updated_at"].isoformat()
        if "expire_at" in user and isinstance(user["expire_at"], datetime):
            user["expire_at"] = user["expire_at"].isoformat()
        return JSONResponse(
            content={
                "status": "success",
                "data": user,
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error getting user by id: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e),
            },
            status_code=500,
        )
