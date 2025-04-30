from pydantic import Field
from typing import Optional
from .BaseModel import BaseDocument


class Comment(BaseDocument):
    content: str = Field("", description="Post's content")
    user_id: str = Field("", description="User's id")
    post_id: str = Field("", description="Post's id")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "John Doe",
                "user_id": "1234567890",
                "post_id": "1234567890",
            }
        }
    }


class Reaction(BaseDocument):
    user_id: str = Field("", description="User's id")
    post_id: str = Field("", description="Post's id")
    type: int = Field(0, description="Type of like", ge=0, lt=5)

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "1234567890",
                "post_id": "1234567890",
                "type": 1,
            }
        }
    }


class Post(BaseDocument):
    content: str = Field("", description="Post's content")
    user_id: str = Field("", description="User's id")
    destination_id: str = Field("", description="Destination's id")
    comment_count: int = Field(0, description="Comment's id")
    reaction_count: int = Field(0, description="User's id who like this post")
    picture: Optional[list[str]] = Field([], description="Picture's url")
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "John Doe",
                "user_id": "1234567890",
                "destination_id": "1234567890",
                "comment_count": 1,
                "reaction_count": 1,
                "picture": ["https://example.com/picture.jpg"],
            }
        }
    }
