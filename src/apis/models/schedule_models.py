from pydantic import Field
from typing import Optional
from datetime import datetime
from .BaseModel import BaseDocument


class Schedule(BaseDocument):
    id: Optional[str] = Field("", description="Activity's id")
    user_id: str = Field("", description="User's id")
    activity_category: str = Field("", description="Activity's category")
    description: str = Field("", description="Activity's description")
    start_time: Optional[datetime] = Field("", description="Activity's start time")
    end_time: Optional[datetime] = Field("", description="Activity's end time")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "61f7b1b7b3b3b3b3b3b3b3",
                "user_id": "61f7b1b7b3b3b3b3b3b3b3",
                "activity_category": "Study",
                "description": "Study for the final exam",
                "start_time": "2025-01-05T14:00:00.000+00:00",
                "end_time": "2025-01-05T16:00:00.000+00:00",
            }
        }
