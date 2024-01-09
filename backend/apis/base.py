from fastapi import APIRouter

from apis.v1 import route_login, route_user, route_view

api_router = APIRouter()
api_router.include_router(route_user.router, prefix="", tags=["users"])
api_router.include_router(route_view.router, prefix="", tags=["views"])
api_router.include_router(route_login.router, prefix="", tags=["login"])
