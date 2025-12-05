from fastapi import FastAPI
from app.api.v1 import auth, users

app = FastAPI(title="Auth Service", version="1.0.0")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

# Импортируем модели для Alembic (после создания app, чтобы избежать циклических импортов)
from app.models.user import User  # noqa: F401

@app.get("/health")
def health():
    return {"status": "ok"}
