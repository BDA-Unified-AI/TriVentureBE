from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from src.apis.routes.chat_route import router as router_chat
from src.apis.routes.auth_route import router as router_auth
from src.apis.routes.location_route import router as router_location
from src.apis.routes.hotel_route import router as router_hotel
from src.apis.routes.travel_dest_route import router as router_travel_dest
from src.apis.routes.scheduling_router import router as router_scheduling
from src.apis.routes.planner_route import router as router_planner
from src.apis.routes.post_router import router as router_post
from src.apis.routes.comment_route import router as router_comment
from src.apis.routes.reaction_route import router as router_reaction
from src.apis.routes.admin_route import router as router_admin

api_router = APIRouter()
api_router.include_router(router_chat)
api_router.include_router(router_auth)
api_router.include_router(router_location)
api_router.include_router(router_hotel)
api_router.include_router(router_travel_dest)
api_router.include_router(router_scheduling)
api_router.include_router(router_planner)
api_router.include_router(router_post)
api_router.include_router(router_comment)
api_router.include_router(router_reaction)
api_router.include_router(router_admin)

def create_app():
    app = FastAPI(
        docs_url="/",
        title="TriVenture Backend"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
