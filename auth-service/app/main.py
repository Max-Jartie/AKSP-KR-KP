from fastapi import FastAPI
from app.api.v1 import auth, users

app = FastAPI(title="Auth Service", version="1.0.0")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

@app.get("/health")
def health():
    return {"status": "ok"}
