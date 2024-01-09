from datetime import datetime, timedelta
from typing import Optional

from jose import jwt

from core.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """

    We will be receiving a data dictionary with a subject (sub). This sub is ideally an email/username that can uniquely identify each record in the table.
    data dict. might look like {"sub":"ping@fastapitutorial.com"}
    These access tokens will auto-expire in 30 minutes.
    We make use of a secret key and algorithms to encode this data dictionary to get a dedicated access token.


    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
