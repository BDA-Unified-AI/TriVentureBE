from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List
from fastapi.responses import JSONResponse
import pandas as pd
import math
from src.apis.models.user_models import User
from src.apis.models.destination_models import Destination
from src.apis.middlewares.auth_middleware import get_current_user
from src.utils.logger import logger
from src.apis.controllers.destination_controller import (
    destination_recommendation_func,
)
from fastapi.responses import JSONResponse
from src.utils.mongo import DestinationCRUD
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/dest", tags=["Destination"])

user_dependency = Annotated[User, Depends(get_current_user)]
EXCEL_FILE_PATH = "./src/data/destination_1_new_tag.xlsx"


@router.get("/get_tourist")
def get_tourist(page: int = Query(default=1, ge=1)):
    try:
        PAGE_SIZE = 10
        df = pd.read_excel(EXCEL_FILE_PATH)
        required_columns = ["name", "description", "image"]
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400, detail="Missing required columns in Excel file"
            )
        total_items = len(df)
        total_pages = math.ceil(total_items / PAGE_SIZE)
        start_idx = (page - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        paginated_df = df[required_columns].iloc[start_idx:end_idx]
        tourist_data = paginated_df.to_dict(orient="records")
        return JSONResponse(
            content={
                "data": tourist_data,
                "page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "page_size": PAGE_SIZE,
            }
        )
    except Exception as e:
        logger.error(f"Error reading the Excel file: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error reading the Excel file: {str(e)}"
        )


@router.get("/destination_detail")
async def get_destinations(destination_id: str = Query(min_length=1, max_length=50)):
    try:
        destination_data = await DestinationCRUD.find_by_id(destination_id)
        if not destination_data:
            return JSONResponse(
                content={"message": "Destination not found"}, status_code=404
            )
        destination_data.pop("created_at")
        destination_data.pop("updated_at")
        destination_data.pop("expire_at")
        destination_data["id"] = str(destination_data["_id"])
        destination_data.pop("_id")
        print("destination_data", destination_data)
        return JSONResponse(content=destination_data, status_code=200)

    except Exception as e:
        logger.error(f"Error fetching destination: {str(e)}")


@router.get("/paginate")
async def get_paginated_destinations(
    page: int = Query(default=1, ge=1), page_size: int = Query(default=10, ge=1, le=100)
):
    """
    Get paginated destinations from database

    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page

    Returns:
        Paginated list of destinations with pagination metadata
    """
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

        # Process results
        serialized_data = []
        for dest in destination_data:
            dest.pop("created_at")
            dest.pop("updated_at")
            dest.pop("expire_at")

            dest_dict = {
                "id": dest["_id"],
                **{k: v for k, v in dest.items() if k != "_id"},
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


@router.get("/get_tourist_names")
async def get_tourist_names():
    try:
        destination_data = await DestinationCRUD.find_all()
        serialized_data = []
        for dest in destination_data:
            dest.pop("created_at")
            dest.pop("updated_at")
            dest.pop("expire_at")
            dest["id"] = str(dest["_id"])
            dest.pop("_id")
            serialized_data.append(dest)
        return JSONResponse(content={"data": serialized_data}, status_code=200)
    except Exception as e:
        logger.error(f"Error getting tourist names: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting tourist names: {str(e)}"
        )


@router.get("/suggest")
async def destination_suggestion(
    question: str,
    user_id: str = Query(
        default=None, description="User ID for personalized recommendations"
    ),
    top_k: int = Query(default=5, ge=1, description="Number of destinations to return"),
):
    result = await destination_recommendation_func(question, user_id, top_k)
    return JSONResponse(content=result)


@router.post("/")
async def create_destination(
    destination_data: Destination, current_user: user_dependency
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
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


@router.put("/{destination_id}")
async def update_destination(
    destination_id: str, destination_data: dict, current_user: user_dependency
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # Add updated_at timestamp
        destination_data["updated_at"] = datetime.utcnow()

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


@router.delete("/{destination_id}")
async def delete_destination(destination_id: str, current_user: user_dependency):
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


@router.get("/")
async def get_all_destinations(current_user: user_dependency):
    print("current_user", current_user)
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # Get all destinations
        destinations = await DestinationCRUD.find_all()

        # Process results
        serialized_data = []
        for dest in destinations:
            dest.pop("created_at")
            dest.pop("updated_at")
            dest.pop("expire_at")
            dest["id"] = str(dest["_id"])
            dest.pop("_id")
            serialized_data.append(dest)

        return JSONResponse(content={"data": serialized_data}, status_code=200)
    except Exception as e:
        logger.error(f"Error fetching destinations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching destinations: {str(e)}"
        )
