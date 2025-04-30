from src.apis.interfaces.api_interface import Location
from src.apis.models.user_models import User
from src.apis.middlewares.auth_middleware import get_current_user
from src.apis.controllers.location_controller import (
    get_location_details,
    get_nearby_places,
    get_places,
    get_weather,
    get_weather_api,
)
from fastapi import APIRouter, status, Depends, Query
from typing import Annotated
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/location", tags=["Location"])

user_dependency = Annotated[User, Depends(get_current_user)]


@router.post("/details", status_code=status.HTTP_200_OK)
def get_location(body: Location, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    return get_location_details(body.lat, body.long)


@router.post("/nearby", status_code=status.HTTP_200_OK)
def get_nearby(body: Location, user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=404)

    return get_nearby_places(body.lat, body.long, body.radius, body.categories)


@router.post("/places", status_code=status.HTTP_200_OK)
def get_near_places(body: Location):
    return get_places(body.lat, body.long, body.radius, body.categories)


@router.post("/weather", status_code=status.HTTP_200_OK)
def get_weather_with_geo(body: Location):
    return get_weather(body.lat, body.long)


@router.get("/weather_text", status_code=status.HTTP_200_OK)
def get_weather_text(destination: str = Query(..., min_length=3)):
    print("destination", destination)
    return get_weather_api(destination)
