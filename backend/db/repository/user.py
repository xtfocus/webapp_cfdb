from core.config import settings
from core.hashing import Hasher
from db.models.user import User
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from schemas.user import UserCreate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def create_new_user(user: UserCreate, db: Session):
    """
    Create a new user

    If username already exist, raise ValidationError
    """
    user = User(
        email=user.email,
        password=Hasher.get_password_hash(user.password),
        is_active=True,
        is_superuser=False,
    )

    family = settings.FAMILY.split("|")

    if not any([(mem in user.email) for mem in family]):
        raise ValidationError(
            [
                ErrorWrapper(ValueError(user.email), "Unknown Email. Contact admin"),
            ],
            UserCreate,
        )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValidationError(
            [
                ErrorWrapper(ValueError(user.email), "User already exists"),
            ],
            UserCreate,
        )

    db.refresh(user)
    return user
