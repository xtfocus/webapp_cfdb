import json
from typing import Optional

from apis.v1.route_login import authenticate_user, get_current_user
from core.security import create_access_token
from db.repository.user import create_new_user
from db.session import get_userdb
from fastapi import (APIRouter, Depends, Form, Request, Response, responses,
                     status)
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.templating import Jinja2Templates
from pydantic.error_wrappers import ValidationError
from schemas.user import UserCreate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/register")
def register_get(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_userdb),
):
    errors = []
    try:
        user = UserCreate(email=email, password=password)
        create_new_user(user=user, db=db)
        return responses.RedirectResponse(
            "/?alert=Successfully%20Registered", status_code=status.HTTP_302_FOUND
        )
    except (KeyError, ValidationError) as e:
        errors_list = json.loads(e.json())
        for item in errors_list:
            errors.append(item.get("loc")[0] + ": " + item.get("msg"))
        return templates.TemplateResponse(
            "auth/register.html", {"request": request, "errors": errors}
        )


@router.get("/login")
def login_get(
    request: Request,
    alert: Optional[str] = None,
):
    return templates.TemplateResponse(
        "auth/login.html", {"request": request, "alert": alert}
    )


@router.post("/login")
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    userdb: Session = Depends(get_userdb),
):
    errors = []
    user = authenticate_user(email=email, password=password, db=userdb)
    if not user:
        errors.append("Incorrect email or password")
        return templates.TemplateResponse(
            "auth/login.html", {"request": request, "errors": errors}
        )
    access_token = create_access_token(data={"sub": email})
    response = responses.RedirectResponse(
        "/?alert=Successfully Logged In", status_code=status.HTTP_302_FOUND
    )
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )
    return response


@router.get("/logout")
def logout(response: Response):
    response = responses.RedirectResponse(
        "/auth/login?alert=Logged Out", status_code=status.HTTP_302_FOUND
    )

    response.delete_cookie(key="access_token")
    return response


def validate_login(request: Request, userdb: Session = Depends(get_userdb)):
    """
    Validates the user login status by checking the provided
        request's access token.

    Parameters:
    - request (fastapi.Request): The FastAPI request object.
    - userdb (sqlalchemy.orm.Session, optional): The database
        session for user-related operations.

    Returns:
    - fastapi.responses.RedirectResponse: Redirects to the login
        page if the user is not authenticated.
    """
    token = request.cookies.get("access_token")
    _, token = get_authorization_scheme_param(token)

    try:
        get_current_user(token=token, db=userdb)
    except Exception as e:
        response = responses.RedirectResponse(
            "/auth/login/?alert=Please Log In", status_code=status.HTTP_302_FOUND
        )
        response.delete_cookie(key="access_token")

        return response
