from fastapi import APIRouter, status, Depends
from typing import Annotated, Optional, List
from fastapi.responses import JSONResponse
from pydantic import Field
from src.utils.helper import convert_string_date_to_iso, datetime_to_iso_string
from src.apis.models.user_models import User
from src.apis.models.BaseModel import BaseDocument
from src.apis.middlewares.auth_middleware import get_current_user
from src.apis.controllers.scheduling_controller import (
    create_a_activity_controller,
    search_activities_controller,
    update_a_activity_controller,
    delete_activities_controller,
    create_multiple_activities_controller,
)
from src.utils.logger import logger

router = APIRouter(prefix="/scheduling", tags=["Scheduling"])

user_dependency = Annotated[User, Depends(get_current_user)]


class BodyActivity(BaseDocument):
    activity_id: Optional[str] = Field("", description="Activity's id")
    activity_category: Optional[str] = Field("", description="Activity's category")
    description: Optional[str] = Field("", description="Activity's description")
    start_time: Optional[str] = Field("", description="Activity's start time")
    end_time: Optional[str] = Field("", description="Activity's end time")

    class Config:
        json_schema_extra = {
            "example": {
                "activity_id": "61f7b1b7b3b3b3b3b3b3b3b3",
                "activity_category": "Study",
                "description": "Study for the final exam",
                "start_time": "2025-01-05T14:00:00",
                "end_time": "2025-01-05T16:00:00",
            }
        }


@router.post("/create_multiple", status_code=status.HTTP_201_CREATED)
async def create_multiple_activities(body: List[BodyActivity], user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]
    result = await create_multiple_activities_controller(body, user_id)
    return JSONResponse(content=result, status_code=201)


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_activity(body: BodyActivity, user: user_dependency):
    print(body)
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]
    start_time = convert_string_date_to_iso(body.start_time)
    end_time = convert_string_date_to_iso(body.end_time)
    result = await create_a_activity_controller(
        body.activity_id,
        body.activity_category,
        body.description,
        start_time,
        end_time,
        user_id,
    )
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=201)


@router.get("/search", status_code=status.HTTP_200_OK)
async def search_activities(start_time: str, end_time: str, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]

    if start_time and end_time:
        start_time = convert_string_date_to_iso(start_time)
        end_time = convert_string_date_to_iso(end_time)

    result = await search_activities_controller(start_time, end_time, user_id)
    if result["status"] == "error":
        return JSONResponse(content={"message": result["message"]}, status_code=404)
    else:
        for activity in result["message"]:
            activity["start_time"] = datetime_to_iso_string(activity["start_time"])
            activity["end_time"] = datetime_to_iso_string(activity["end_time"])
            activity["created_at"] = datetime_to_iso_string(activity["created_at"])
            activity["updated_at"] = datetime_to_iso_string(activity["updated_at"])
            activity["id"] = activity.pop("_id")
            del activity["user_id"]
        return JSONResponse(content=result, status_code=200)


@router.get("/search_all", status_code=status.HTTP_200_OK)
async def search_activities(user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]
    result = await search_activities_controller(None, None, user_id)
    logger.info(f"result {result}")
    if result["status"] == "error":
        return JSONResponse(content={"message": result["message"]}, status_code=404)
    else:
        for activity in result["message"]:
            activity["start_time"] = datetime_to_iso_string(activity["start_time"])
            activity["end_time"] = datetime_to_iso_string(activity["end_time"])
            activity["created_at"] = datetime_to_iso_string(activity["created_at"])
            activity["updated_at"] = datetime_to_iso_string(activity["updated_at"])
            activity["id"] = activity.pop("_id")
            del activity["user_id"]
        return JSONResponse(content=result, status_code=200)


@router.put("/update", status_code=status.HTTP_200_OK)
async def update_activity(body: BodyActivity, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]
    if body.start_time and body.end_time:
        start_time = convert_string_date_to_iso(body.start_time)
        end_time = convert_string_date_to_iso(body.end_time)
        result = await update_a_activity_controller(
            body.activity_id,
            body.activity_category,
            body.description,
            start_time,
            end_time,
            user_id,
        )
        if result["status"] == "error":
            return JSONResponse(content=result, status_code=404)
        else:
            return JSONResponse(content=result, status_code=200)
    else:
        return JSONResponse(
            content={"message": "Start time and end time are required"}, status_code=404
        )


@router.delete("/delete", status_code=status.HTTP_200_OK)
async def delete_activity(activity_id: str, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    user_id = user["id"]
    result = await delete_activities_controller(activity_id, None, None, user_id)
    if result["status"] == "error":
        return JSONResponse(content=result, status_code=404)
    else:
        return JSONResponse(content=result, status_code=200)
