from src.apis.models.user_models import User
from src.apis.middlewares.auth_middleware import get_current_user
from fastapi import APIRouter, status, Depends
from typing import Annotated
from fastapi.responses import StreamingResponse
from src.apis.interfaces.api_interface import Planning
from src.apis.controllers.planner_controller import message_generator
import json
from fastapi import BackgroundTasks

router = APIRouter(prefix="/planner", tags=["Planner"])

user_dependency = Annotated[User, Depends(get_current_user)]

config = {
    "configurable": {
        "user_id": "673b0d33549989f756fa3970",
        "user_email": "baohtqe170017@fpt.edu.vn",
        "contact_number": "1234567890",
        "session_id": "6d16c975e8b74d979d6d680e6ff536eb",
        "lat": 13.717163281669754,
        "long": 109.21053970482858,
    }
}

@router.post("/invoke")
async def invoke_planner(body: Planning, background: BackgroundTasks):
    input_graph = {
        "duration": body.duration,
        "start_date": body.start_date,
        "location": body.location,
        "interests": body.interests,
        "nation": body.nation,
        "include_destination": body.include_destination,
        "limit_interation": body.limit_interation,
        "current_interation": 0,
        "error": None,
    }
    return StreamingResponse(
        message_generator(input_graph, config, background),
        media_type="text/plain",
    )
