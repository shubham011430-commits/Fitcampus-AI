import warnings
from typing import List

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "fitcampus"
    mysql_password: str = "Shubham@123456"
    mysql_db: str = "fitcampus"

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "AI_API_KEY"),
    )

    ai_model: str = "gemini-3.8-flash"
    cors_origins: str = (
        "http://localhost:5500,http://127.0.0.1:5500"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def check_secrets(self):
        if len(self.jwt_secret) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters."
            )

        if not self.gemini_api_key:
            warnings.warn(
                "No GEMINI_API_KEY set: AI features use rule-based fallbacks."
            )

        return self

    @property
    def cors_origin_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+aiomysql",
            username=self.mysql_user,
            password=self.mysql_password,
            host=self.mysql_host,
            port=self.mysql_port,
            database=self.mysql_db,
        )


settings = Settings()