from db.repository.user import create_new_user
from db.session import get_userdb as get_db
from fastapi import APIRouter, Depends, status  # modified
from schemas.user import ShowUser, UserCreate  # modified
from sqlalchemy.orm import Session

router = APIRouter()


# modified
@router.post("/", response_model=ShowUser, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    user = create_new_user(user=user, db=db)
    return user
