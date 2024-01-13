from apps.v1.route_login import validate_login
from db.repository import chart
from db.session import get_knowledgebase, get_userdb
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/summary/editor/activity")
async def editor_activity_chart(
    request: Request,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    Show the number of rows updated per editor per day as line charts

    """
    response = validate_login(request, userdb)
    if response:
        return response

    dfs = chart.editor_activity()
    for table_name, data in dfs.items():
        chart.create_activity_chart(
            data, table_name, f"static/chart/activity_{table_name}.png"
        )
    return templates.TemplateResponse(
        "chart/activity.html", {"request": request, "table_names": list(dfs)}
    )
