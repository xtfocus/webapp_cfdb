from core.config import settings
from core.hashing import Hasher
from db.models.user import User
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from schemas.user import UserCreate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def check_familiar_name(email: str):
    """
    Raise Error if the email doesn't contain known names
    """
    family = settings.FAMILY.split("|")

    if not any([(mem in email) for mem in family]):
        raise ValidationError(
            [
                ErrorWrapper(ValueError(email), "Unknown Email. Contact admin"),
            ],
            UserCreate,
        )


def reject_familiar_name(email: str, db: Session):
    """
    Check if user already have an account under User

    This is to make sure each person has only one account

    """

    family = settings.FAMILY.split("|")

    for mem in family:
        if mem in email:
            if db.query(User).filter(User.email.contains(mem)).first():
                raise ValidationError(
                    [
                        ErrorWrapper(
                            ValueError(email), "Unsupported Email. Contact admin"
                        ),
                    ],
                    UserCreate,
                )


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

    check_familiar_name(user.email)

    reject_familiar_name(user.email, db)

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
