import os
from pathlib import Path
from string import Template

from dotenv import load_dotenv

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    PROJECT_NAME: str = "Hua Hin Man 🔥"
    PROJECT_VERSION: str = "1.0.0"

    DB_USER: str = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_SERVER: str = os.getenv("DB_SERVER")
    DB_PORT: str = os.getenv("DB_PORT", 1433)  # Default mssql
    USERNAME_DB: str = os.getenv("USERNAME_DB")
    KNOWLEDGE_DB: str = os.getenv("KNOWLEDGE_DB")

    # Use an f-string within the string template
    BASE_DB_URL_TEMPLATE = Template(
        f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/$DB_NAME?driver=ODBC+Driver+17+for+SQL+Server"
    )

    # Use the string template to substitute values and generate database URLs
    USERNAME_DB_URL = BASE_DB_URL_TEMPLATE.substitute(DB_NAME=USERNAME_DB)
    KNOWLEDGE_DB_URL = BASE_DB_URL_TEMPLATE.substitute(DB_NAME=KNOWLEDGE_DB)

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TIMEOUT"))  # in mins
    FAMILY = os.getenv("FAMILY")


settings = Settings()
