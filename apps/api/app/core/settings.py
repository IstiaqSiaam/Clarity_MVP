from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    api_port: int = 8000
    jwt_secret: str = "changeme"
    postgres_url: str = "postgresql://clarity:clarity@localhost:5432/clarity"
    mongo_url: str = "mongodb://clarity:clarity@localhost:27017/?authSource=admin"
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
