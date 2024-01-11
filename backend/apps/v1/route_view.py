from typing import List, Optional

from apis.v1.route_login import get_current_user
from apps.v1.route_login import validate_login
from db.models.table import StandardName, TableName
from db.repository import view
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

vi_term_path = Path(
    default=..., description="any possible Vietnamese clinical-finding term"
)


@router.get("/table/names", response_model=List[str])
async def get_table_names(
    request: Request,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    Get a list of available table names.
    """
    response = validate_login(request, userdb)
    if response:
        return response

    return [table_name.value for table_name in TableName]


@router.get("/")
def home(
    request: Request, alert: Optional[str] = None, userdb: Session = Depends(get_userdb)
):
    return templates.TemplateResponse(
        "view/home.html", {"request": request, "alert": alert}
    )


@router.get("/test_private/{id}")
def view_detail(request: Request, id: int, userdb: Session = Depends(get_userdb)):
    token = request.cookies.get("access_token")
    _, token = get_authorization_scheme_param(token)

    try:
        author = get_current_user(token=token, db=userdb)

        view = {
            "title": "Secret message",
            "Content": "Hello there",
            "id": id,
        }
        return view
    except Exception as e:
        errors = ["Please log"]
        view = {"title": "error", "content": "error content"}
        return templates.TemplateResponse(
            "view/detail.html",
            {"request": request, "errors": errors, "view": view},
        )


@router.get("/table/summary/{table_name}")
async def table_summary(
    request: Request,
    table_name: TableName,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    Showing table information including number of rows, columns, PK, FK, etc.
    """
    response = validate_login(request, userdb)
    if response:
        return response

    db_table = view.get_table(table_name.value)
    return_dict = view.get_table_summary(db, db_table)

    return return_dict


@router.get("/concept/vi/{vi_term}")
async def discover_vi_term(
    request: Request,
    vi_term: str = vi_term_path,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
        If Vietnamese term vi_term is not a known vn_main or vn_synonym,
    return error
        else, return the details of the concept

    """
    response = validate_login(request, userdb)
    if response:
        return response

    vn_main, en_main, vn_synonyms, en_synonyms, en_main_vsrc = view.locate_vn_term(
        vi_term
    )

    if vn_main is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{vi_term} not found in database",
        )
    return {
        "vn_main": vn_main,
        "en_main": en_main,
        "vn_synonyms": vn_synonyms,
        "en_synonyms": en_synonyms,
        "en_main_vsrc": en_main_vsrc,
    }


@router.get("/summary/editor/insert_count")
async def editor_insert_counts(
    request: Request,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    Show the number of inserted rows contributed per editor
    """
    response = validate_login(request, userdb)
    if response:
        return response

    result = view.rows_per_editors(mode="insert")
    return result


@router.get("/summary/editor/update_count")
async def editor_update_counts(
    request: Request,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    Show the number of updated rows contributed per editor
    """
    response = validate_login(request, userdb)
    if response:
        return response

    result = view.rows_per_editors(mode="update")
    return result


# The path parameter to be used in following routes
en_term_path = Path(
    default=..., description="any possible English clinical finding term"
)


@router.get("/concept/en/{en_term}")
async def discover_en_term(
    request: Request,
    en_term: str = en_term_path,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    If English term en_term is not a known en_main or en_synonym, return error
    else, return the details of the concept
    """
    response = validate_login(request, userdb)
    if response:
        return response

    vn_main, en_main, vn_synonyms, en_synonyms, en_main_vsrc = view.locate_en_term(
        en_term
    )
    if en_main is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{en_term} not found in database",
        )

    return {
        "vn_main": vn_main,
        "en_main": en_main,
        "vn_synonyms": vn_synonyms,
        "en_synonyms": en_synonyms,
        "en_main_vsrc": en_main_vsrc,
    }


@router.get("/term/vi/{vi_term}")
async def check_vn_term_exist(
    request: Request,
    vi_term: str = vi_term_path,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
) -> bool:
    """
    Check if Vietnamese term vn_term exists in the database
    """
    response = validate_login(request, userdb)
    if response:
        return response

    found = False
    with engine.connect() as conn:
        if view.vn_synonym_to_vn_main(conn, vi_term) or view.vn_main_in_dictionary(
            conn, vi_term
        ):
            found = True

    return found


@router.get("/term/en/{en_term}")
async def check_en_term_exist(
    request: Request,
    en_term: str = en_term_path,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    Check if English term en_term exists in the database
    """
    response = validate_login(request, userdb)
    if response:
        return response

    found = False
    with engine.connect() as conn:
        if view.en_main_in_dictionary(conn, en_term) or view.en_synonym_to_en_main(
            conn, en_term
        ):
            found = True

    return found


@router.get("/status/validate")
async def validation_status(
    request: Request,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    Showing validation status of the en_main values in the dictionary table
    """

    response = validate_login(request, userdb)
    if response:
        return response
    return view.validated_en_main_statistics(view.en_vsrc_tables)


@router.get("/status/uncharted_en_main")
async def uncharted_en_main(
    request: Request,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    Showing the en_main values in the dictionary that are not mapped to any validation sources
    """
    response = validate_login(request, userdb)
    if response:
        return response
    return {
        "uncharted_en_mains": view.calculate_non_validated_en_main(view.en_vsrc_tables)
    }


@router.get("/daily_review")
async def review_home(
    request: Request,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    response = validate_login(request, userdb)
    if response:
        return response

    table_names = [table_name.value for table_name in TableName]
    return templates.TemplateResponse(
        "view/review.html", {"request": request, "tableNames": table_names}
    )


@router.get("/review/{table_name}")
async def review_table_by_day(
    request: Request,
    table_name: TableName,
    date: str = None,
    mode: str = "update",
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    """
    FastAPI route to review daily records from a specified table.

    Parameters:
    - table_name (str): Name of the table to review.
    - date (str, optional): Date in YMD format, e.g., "2023-12-31".
        If not provided, the latest date from the table will be used.
    - mode (str, optional): Operation mode, either "insert" or "update".

    Returns:
    - dict: A dictionary containing the result or {"msg": "empty"} if the result is None.
    """

    response = validate_login(request, userdb)
    if response:
        return response

    table_names = [table_name.value for table_name in TableName]

    db_table = view.get_table(table_name.value)

    result = view.review_per_day(db_table, date, mode)

    if result:
        return templates.TemplateResponse(
            "view/review.html",
            {"request": request, "data": result, "tableNames": table_names},
        )

    else:
        return {"msg": "empty"}


@router.get("/std/{stdid}")
async def locate_standard_id(
    request: Request,
    stdid: str,
    glossary: Optional[StandardName] = None,
    db: Session = Depends(get_knowledgebase),
    userdb: Session = Depends(get_userdb),
):
    response = validate_login(request, userdb)
    if response:
        return response
    match = locate_standard(stdid, glossary)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{stdid} not found in database",
        )
    else:
        vn_main, en_main, vn_synonyms, en_synonyms, en_main_vsrc = match

        return {
            "vn_main": vn_main,
            "en_main": en_main,
            "vn_synonyms": vn_synonyms,
            "en_synonyms": en_synonyms,
            "en_main_vsrc": en_main_vsrc,
        }
