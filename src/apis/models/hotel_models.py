from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime
from .BaseModel import BaseDocument


class BookHotel(BaseDocument):
    hotel_name: str = Field("", description="Hotel's name")
    address: str = Field("", description="Hotel's address")
    phone_number: str = Field("", description="Hotel's phone number")
    hotel_email: EmailStr = Field("", description="Hotel's email")
    start_time: Optional[datetime] = Field("", description="Start time of the booking")
    end_time: Optional[datetime] = Field("", description="End time of the booking")
    rating: str = Field("", description="Hotel's rating")
    website: str = Field("", description="Hotel's website")

    class Config:
        json_schema_extra = {
            "example": {
                "hotel_name": "Blue Lagoon Resort",
                "address": "123 Beachside Blvd, Paradise City, Island Nation 54321",
                "phone_number": "+1234567890",
                "hotel_email": "baohtqe170017@fpt.edu.vn",
                "start_time": "2025-01-05T14:00:00.000+00:00",
                "end_time": "2025-01-10T11:00:00.000+00:00",
                "rating": "4.5",
                "website": "https://www.bluelagoonresort.com",
            }
        }
