from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from typing import Annotated
from src.apis.models.user_models import User
from src.apis.controllers.auth_controller import login_control
from src.apis.controllers.user_controller import (
    list_users_controller,
    update_user_controller,
    delete_user_controller,
    get_user_by_id_controller,
)
from src.apis.interfaces.auth_interface import _LoginResponseInterface
from src.apis.interfaces.auth_interface import Credential
from src.apis.middlewares.auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentications"])

user_dependency = Annotated[User, Depends(get_current_user)]


@router.post(
    "/login", status_code=status.HTTP_200_OK, response_model=_LoginResponseInterface
)
async def login(credential: Credential):
    try:
        token, user_data, first_login = await login_control(credential.credential)
        return JSONResponse(
            content={
                "token": token,
                "user_data": user_data,
                "first_login": first_login,
            },
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)


@router.get("/get_info", status_code=status.HTTP_200_OK)
async def get_user_info(user: user_dependency):
    if user is None:
        return JSONResponse(content={"message": "User not found"}, status_code=401)
    return JSONResponse(content={"user": user}, status_code=200)


@router.get("/users", status_code=status.HTTP_200_OK)
async def get_users():
    return await list_users_controller()


@router.put("/users/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(user_id: str, user_data: dict):
    return await update_user_controller(user_id, user_data)


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: str):
    return await delete_user_controller(user_id)


@router.get("/users/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_by_id(user_id: str):
    return await get_user_by_id_controller(user_id)
