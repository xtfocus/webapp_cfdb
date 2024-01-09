from passlib.context import CryptContext


class Hasher:
    """
    A class providing static methods for password hashing and verification using bcrypt.

    Methods:
        verify_password(plain_password, hashed_password):
            Verify if a plain password matches a hashed password.

        get_password_hash(password):
            Generate a hashed password for a given plain password.

    Example:
    --------
    >>> Hasher.get_password_hash("supersecret1234")
    '$2b$12$qFVOexqUL3/qhlHwy8W8eu0S80hxq2h382cTQrJyqyDJiJlCVRBhe'

    >>> Hasher.verify_password("supersecret1234", "$2b$12$qFVOexqUL3/qhlHwy8W8eu0S80hxq2h382cTQrJyqyDJiJlCVRBhe")
    True
    """

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(
            plain_password, hashed_password
        )

    @staticmethod
    def get_password_hash(password):
        return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)
