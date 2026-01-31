import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class ApplicationSettings(BaseModel):
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    DATABASE_PREFIX: str = "postgresql+asyncpg"

    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: int = os.getenv("POSTGRES_PORT")
    POSTGRES_DATABASE_NAME: str = os.getenv("POSTGRES_DATABASE_NAME")

    DATABASE_CONNECTION_STRING: str = (
        f"{DATABASE_PREFIX}://{POSTGRES_USER}:" f"{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE_NAME}"
    )


application_settings = ApplicationSettings()
