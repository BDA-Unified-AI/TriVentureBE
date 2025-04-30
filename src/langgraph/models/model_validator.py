from pydantic import BaseModel, Field, EmailStr


# from typing import Optional
# from datetime import datetime, timezone


# class BaseDocument(BaseModel):
#     created_at: Optional[datetime] = Field(
#         default_factory=lambda: datetime.now(timezone.utc)
#     )
#     updated_at: Optional[datetime] = Field(
#         default_factory=lambda: datetime.now(timezone.utc)
#     )

#     class Config:
#         arbitrary_types_allowed = True

# class Activity(BaseDocument):
#     id: Optional[str] = Field("", description="Activity's id")
#     user_id: str = Field("", description="User's id")
#     activity_category: str = Field("", description="Activity's category")
#     description: str = Field("", description="Activity's description")
#     start_time: Optional[datetime] = Field("", description="Activity's start time")
#     end_time: Optional[datetime] = Field("", description="Activity's end time")


# class BookHotel(BaseDocument):
#     hotel_name: str = Field("", description="Hotel's name")
#     address: str = Field("", description="Hotel's address")
#     phone_number: str = Field("", description="Hotel's phone number")
#     hotel_email: EmailStr = Field("", description="Hotel's email")
#     start_time: Optional[datetime] = Field("", description="Start time of the booking")
#     end_time: Optional[datetime] = Field("", description="End time of the booking")
#     rating: str = Field("", description="Hotel's rating")
#     website: str = Field("", description="Hotel's website")

#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "hotel_name": "Blue Lagoon Resort",
#                 "address": "123 Beachside Blvd, Paradise City, Island Nation 54321",
#                 "phone_number": "+1234567890",
#                 "hotel_email": "baohtqe170017@fpt.edu.vn",
#                 "start_time": "2025-01-05T14:00:00.000+00:00",
#                 "end_time": "2025-01-10T11:00:00.000+00:00",
#                 "rating": "4.5",
#                 "website": "https://www.bluelagoonresort.com",
#             }
#         }


class NearlyDestinationRecommendation(BaseModel):
    query: str = Field(
        ...,
        title="Query related to wanting to go somewhere",
        description="Auto extracted from user's message. Using Vietnamese language for better results.",
    )
    places: str = Field(..., title="Places", description="place mention in query")
    kinds: str = Field(
        ...,
        title="Kinds",
        description="""
        Kinds of places you want to find choose one of options: 
        ["architecture", "historic", "cultural", "natural", "sport", "religion", "accomodations", "foods", "shops", "other"]""",
    )

    class Config:
        json_schema_extra = {
            "example": {"query": "Địa điểm gần Hà Nội" "places" "Hà Nội"}
        }
