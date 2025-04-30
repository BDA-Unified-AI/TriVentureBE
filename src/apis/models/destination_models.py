from pydantic import Field
from typing import Literal
from .BaseModel import BaseDocument
from bson import ObjectId


class Destination(BaseDocument):
    name: str = Field("", description="Destination's name")
    description: str = Field("", description="Destination's description")
    image: str = Field("", description="Destination's picture")
    created_user_id: str = Field("", description="Destination's created user")
    updated_user_id: str = Field("", description="Destination's updated user")
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Hanoi",
                "description": "Hanoi is the capital of Vietnam",
                "image": "https://www.google.com.vn",
                "created_user_id": "1234567890",
                "updated_user_id": "1234567890",
            }
        }
    }
