from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_url: str 
    mongodb_database: str = "svas"
    jwt_secret_key: str = "svasya-secret-jwt-key-2026-super-secure"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()