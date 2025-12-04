from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://rental_user:rental_pass@db:5432/rental_db"
    JWT_SECRET_KEY: str = "Project_secret_key"
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
