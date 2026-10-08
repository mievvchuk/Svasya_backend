from typing import Union
import json
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_url: str 
    mongodb_database: str = "svas"
    jwt_secret_key: str = "svasya-secret-jwt-key-2026-super-secure"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours
    cors_origins: Union[list[str], str] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    return json.loads(v_stripped)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"


settings = Settings()