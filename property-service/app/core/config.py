from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://rental_user:rental_pass@db:5432/rental_db"

    class Config:
        env_file = ".env"

settings = Settings()
