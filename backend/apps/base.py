from fastapi import APIRouter

from apps.v1 import route_chart, route_login, route_view

app_router = APIRouter()


app_router.include_router(
    route_view.router, prefix="", tags=[""], include_in_schema=False
)

app_router.include_router(
    route_chart.router, prefix="", tags=["chart"], include_in_schema=False
)


app_router.include_router(
    route_login.router, prefix="/auth", tags=[""], include_in_schema=False
)
