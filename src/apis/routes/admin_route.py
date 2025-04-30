from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List
from fastapi.responses import JSONResponse
import pandas as pd
import math
from src.apis.models.user_models import User
from src.apis.models.destination_models import Destination
from src.apis.middlewares.auth_middleware import get_current_user
from src.utils.logger import logger
from fastapi import status
from src.utils.mongo import DestinationCRUD, PostCRUD, UserCRUD
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/admin", tags=["Admin"])

user_dependency = Annotated[User, Depends(get_current_user)]

@router.get("/destination/paginate")
async def get_paginated_destinations(
    user: user_dependency,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100)
):
    """
    Get paginated destinations from database

    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page

    Returns:
        Paginated list of destinations with pagination metadata
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # Calculate skip value for pagination
        skip = (page - 1) * page_size

        # Query destinations with pagination
        destination_data = await DestinationCRUD.find_many(
            filter={},  # Empty filter means get all
            skip=skip,
            limit=page_size,
            sort=[("created_at", -1)],  # Sort by created_at descending
        )

        # Get total count for pagination metadata
        total_items = await DestinationCRUD.count({})
        total_pages = math.ceil(total_items / page_size)

        # Collect unique user IDs
        user_ids = set()
        for dest in destination_data:
            if dest.get("created_user_id"):
                user_ids.add(dest["created_user_id"])
            if dest.get("updated_user_id"):
                user_ids.add(dest["updated_user_id"])

        # Fetch all users in a single query
        users = {}
        if user_ids:
            user_data = await UserCRUD.find_many(
                filter={"_id": {"$in": [ObjectId(uid) for uid in user_ids]}}
            )
            users = {str(user["_id"]): user for user in user_data}

        # Process results
        serialized_data = []
        for dest in destination_data:
            # Convert timestamps to ISO format
            if "created_at" in dest:
                dest["created_at"] = dest["created_at"].isoformat() if dest["created_at"] else None
            if "updated_at" in dest:
                dest["updated_at"] = dest["updated_at"].isoformat() if dest["updated_at"] else None
            dest.pop("expire_at", None)

            dest_dict = {
                "id": dest["_id"],
                "created_user": {
                    "id": dest.get("created_user_id"),
                    "name": users.get(dest.get("created_user_id", ""), {}).get("name"),
                    "email": users.get(dest.get("created_user_id", ""), {}).get("email")
                } if dest.get("created_user_id") else None,
                "updated_user": {
                    "id": dest.get("updated_user_id"),
                    "name": users.get(dest.get("updated_user_id", ""), {}).get("name"),
                    "email": users.get(dest.get("updated_user_id", ""), {}).get("email")
                } if dest.get("updated_user_id") else None,
                **{k: v for k, v in dest.items() if k not in ["_id", "created_user_id", "updated_user_id"]},
            }
            serialized_data.append(dest_dict)

        return JSONResponse(
            content={
                "data": serialized_data,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "page_size": page_size,
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error fetching paginated destinations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching paginated destinations: {str(e)}"
        )



@router.post("/destination")
async def create_destination(
    destination_data: Destination, current_user: user_dependency
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        destination_data.created_user_id = current_user["id"]
        destination_data.updated_user_id = current_user["id"]
        destination_id = await DestinationCRUD.create(destination_data.model_dump())

        if not destination_id:
            raise HTTPException(status_code=400, detail="Failed to create destination")

        return JSONResponse(
            content={
                "message": "Destination created successfully",
                "id": destination_id,
            },
            status_code=201,
        )
    except Exception as e:
        logger.error(f"Error creating destination: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error creating destination: {str(e)}"
        )


@router.put("/destination/{destination_id}")
async def update_destination(
    destination_id: str, destination_data: dict, current_user: user_dependency
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # Add updated_at timestamp
        destination_data["updated_at"] = datetime.utcnow()
        destination_data["updated_user_id"] = current_user["id"]
        # Update destination
        result = await DestinationCRUD.update(
            {"_id": ObjectId(destination_id)}, destination_data
        )

        if not result:
            raise HTTPException(status_code=404, detail="Destination not found")

        return JSONResponse(
            content={"message": "Destination updated successfully"}, status_code=200
        )
    except Exception as e:
        logger.error(f"Error updating destination: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating destination: {str(e)}"
        )


@router.delete("/destination/{destination_id}")
async def delete_destination(destination_id: str, current_user: user_dependency):
    print("destination_id", destination_id)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # Delete destination
        result = await DestinationCRUD.delete_one({"_id": ObjectId(destination_id)})

        if not result:
            raise HTTPException(status_code=404, detail="Destination not found")

        return JSONResponse(
            content={"message": "Destination deleted successfully"}, status_code=200
        )
    except Exception as e:
        logger.error(f"Error deleting destination: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting destination: {str(e)}"
        )



@router.delete("/post/delete/{post_id}", status_code=status.HTTP_200_OK)
async def delete_post(post_id: str, user: user_dependency):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    result = await PostCRUD.delete_one({"_id": ObjectId(post_id)})
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    return JSONResponse(content={"message": "Post deleted successfully"}, status_code=200)
