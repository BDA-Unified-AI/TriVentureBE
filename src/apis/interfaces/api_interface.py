from pydantic import BaseModel, Field
from typing import Optional
from src.apis.models.BaseModel import BaseDocument
from typing import List, Union


class Chat(BaseModel):
    message: str = Field(..., title="Message from user")
    session_id: Optional[str] = Field(None, title="Session Id")
    history: Optional[list] = Field(None, title="Chat history")
    lat: Optional[float] = Field(None, title="Latitude")
    long: Optional[float] = Field(None, title="Longitude")
    intent: Optional[str] = Field(None, title="Intent")
    language: Optional[str] = Field("en", title="Language")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Đề xuất cho 1 địa điểm",
                "session_id": "6d16c975e8b74d979d6d680e6ff536eb",
                "history": [
                    {"content": "tìm khách sạn xịn ở QUy Nhơn", "type": "human"},
                    {
                        "content": "search_hotels_luxury  on frontend for user to select",
                        "type": "ai",
                    },
                ],
                "lat": 13.717162954654036,
                "long": 109.21054173319894,
                "intent": None,
                "language": "Vietnamese",
            }
        }


class ChatHistory(BaseModel):
    session_id: Optional[str] = Field(None, title="Session Id")

    class Config:
        json_schema_extra = {"example": {"session_id": "6701fe32d76fde9d8df1de8e"}}


class ChatHistoryManagement(BaseDocument):
    session_id: str = Field("6701fe32d76fde9d8df1de8e", title="Session Id")
    user_id: str = Field("6701fe32d76fde9d8df1de8e", title="User Id")
    intent: Optional[str] = Field(None, title="Intent")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "6701fe32d76fde9d8df1de8e",
                "user_id": "6701fe32d76fde9d8df1de8e",
                "intent": "greeting",
            }
        }


class Location(BaseModel):
    lat: float = Field(13.717162954654036, title="Latitude")
    long: float = Field(109.21054173319894, title="Longitude")
    radius: Optional[int] = Field(5000, title="Radius in meters")
    location_text: Optional[str] = Field("Hanoi", title="Location text")
    categories: Optional[str] = Field("interesting_places", title="Type of places")

    class Config:
        json_schema_extra = {
            "example": {
                "lat": 13.717162954654036,
                "long": 109.21054173319894,
                "radius": 5000,
                "location_text": "Hanoi",
                "categories": "interesting_places",
            }
        }


class Destination(BaseModel):
    id: Optional[str] = Field(..., title="Destination Id", min_length=0)
    name: Optional[str] = Field(..., title="Destination Name", min_length=1)
    description: Optional[str] = Field(..., title="Description", min_length=0)
    image: Optional[str] = Field(..., title="Image", min_length=0)


class Planning(BaseModel):
    duration: str = Field("7", title="Duration")
    start_date: str = Field("June 1-7", title="Start date")
    end_date: str = Field("June 1-7", title="End date")
    location: str = Field("Quy Nhon, Vietnam", title="Location")
    interests: str = Field("natural, cultural", title="Interests")
    nation: str = Field("Vietnamese", title="Nation")
    include_destination: Optional[List[Union[Destination, str]]] = Field(
        [], title="Include destinations"
    )
    limit_interation: Optional[int] = Field(3, title="Limit interation")

    class Config:
        json_schema_extra = {
            "example": {
                "duration": "7",
                "start_date": "June 1-7",
                "location": "Quy Nhon, Vietnam",
                "interests": "natural, cultural",
                "nation": "nation",
                "include_destination": {
                    "destination": "Ky Co Beach",
                    "description": "Ky Co Beach is a beautiful beach in Quy Nhon, Vietnam",
                },
                "limit_interation": 3,
            }
        }


{
    "duration": "6",
    "start_date": "2025-03-18",
    "end_date": "2025-03-24",
    "include_destination": [
        {"id": "", "name": "KHU DÃ NGOẠI TRUNG LƯƠNG", "description": "", "image": ""},
        {"id": "", "name": "NÚI VŨNG CHUA", "description": "", "image": ""},
    ],
    "interests": "natural, cultural",
    "location": "Quy Nhon, Vietnam",
    "nation": "Vietnamese",
    "limit_interation": 5,
}
