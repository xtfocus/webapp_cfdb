from typing import Generator

from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

USERNAME_SQLALCHEMY_DATABASE_URL = settings.USERNAME_DB_URL
userdb_engine = create_engine(USERNAME_SQLALCHEMY_DATABASE_URL)

KNOWLEDGE_SQLALCHEMY_DATABASE_URL = settings.KNOWLEDGE_DB_URL
knowledgebase_engine = create_engine(KNOWLEDGE_SQLALCHEMY_DATABASE_URL)


UserdbSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=userdb_engine)

KnowledgebaseSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=knowledgebase_engine
)


def get_userdb() -> Generator:
    try:
        db = UserdbSessionLocal()
        yield db
    finally:
        db.close()


def get_knowledgebase() -> Generator:
    try:
        db = KnowledgebaseSessionLocal()
        yield db
    finally:
        db.close()
