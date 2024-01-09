from apis.v1.route_login import get_current_user
from db.models.user import User
from db.session import get_userdb
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/test/{id}")
def protected_one(
    id: int,
    userdb: Session = Depends(get_userdb),
    current_user: User = Depends(get_current_user),
):
    print("debug0")
    message = show_test_private(id, db=userdb)
    print("debug1", message)
    return {"message": message}
