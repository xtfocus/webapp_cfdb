from typing import List, Optional

from apis.v1.route_login import get_current_user
from apps.v1.route_login import validate_login
from db.models.table import StandardName, TableName
from db.repository import chart, view
from db.repository.view import locate_standard
from db.session import get_knowledgebase, get_userdb
from db.session import knowledgebase_engine as engine
from fastapi import (APIRouter, Depends, HTTPException, Path, Request,
                     responses, status)
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/summary/editor/activity")
async def editor_activity_chart(request: Request):
    """
    Show the number of rows updated per editor per day as line charts

    """
    dfs = chart.editor_activity()
    for table_name, data in dfs.items():
        chart.create_activity_chart(
            data, table_name, f"static/chart/activity_{table_name}.png"
        )
    return templates.TemplateResponse(
        "chart/activity.html", {"request": request, "table_names": list(dfs)}
    )
