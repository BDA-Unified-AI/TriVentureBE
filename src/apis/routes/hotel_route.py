from fastapi import APIRouter, status, Depends, BackgroundTasks
from typing import Annotated
from fastapi.responses import JSONResponse
from src.apis.controllers.hotel_controller import (
    book_hotel_controller,
    send_booking_confirmation_email,
)
from src.apis.models.user_models import User
from src.apis.middlewares.auth_middleware import get_current_user
from src.utils.logger import logger
from pydantic import BaseModel, Field
import pandas as pd

router = APIRouter(prefix="/hotel", tags=["Hotel"])

user_dependency = Annotated[User, Depends(get_current_user)]


from src.apis.models.hotel_models import BookHotel


@router.post("/book_hotel", status_code=status.HTTP_201_CREATED)
async def book_hotel(
    body: BookHotel,
    user: user_dependency,
    background_tasks: BackgroundTasks,
):
    logger.info(f"User: {user}")
    if user is None:
        return JSONResponse(
            content="User not found", status_code=status.HTTP_401_UNAUTHORIZED
        )
    hotel_email = "baohtqe170017@fpt.edu.vn"
    user_id = user["id"]
    user_email = user["email"]
    user_contact_number = user.get("contact_number", "Does not have contact number")
    response = await book_hotel_controller(
        body.hotel_email,
        body.hotel_name,
        body.address,
        body.phone_number,
        body.website,
        body.start_time,
        body.end_time,
        user_id,
    )
    if response["status"] == "error":
        return JSONResponse(
            content=response["message"], status_code=status.HTTP_400_BAD_REQUEST
        )
    background_tasks.add_task(
        send_booking_confirmation_email,
        user_email,
        user_contact_number,
        hotel_email,
        body.start_time,
        body.end_time,
    )
    return JSONResponse(content=response["message"], status_code=status.HTTP_200_OK)


df = pd.read_excel("./src/data/hotel.xlsx")


class HotelRequest(BaseModel):
    hotel_type: str = Field(..., title="Type of hotel")
    top_k: int = Field(5, title="Number of hotels to return")

    class Config:
        json_schema_extra = {
            "example": {
                "hotel_type": "popular",
                "top_k": 5,
            }
        }


@router.post("/search_hotels")
def search_hotels(request: HotelRequest):
    if request.hotel_type not in ["popular", "luxury", "basic"]:
        return {
            "error": "Invalid hotel type. Choose from 'popular', 'luxury', 'basic'."
        }
    filtered_df = df[df["type"] == request.hotel_type]
    top_hotels = filtered_df.head(request.top_k).to_dict(orient="records")

    return JSONResponse(content=top_hotels, status_code=status.HTTP_200_OK)
