from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_url: str 
    mongodb_database: str = "store_db"

    class Config:
        env_file = ".env"


settings = Settings()