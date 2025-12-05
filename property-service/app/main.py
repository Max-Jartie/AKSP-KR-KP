from fastapi import FastAPI
from app.api.v1 import properties, units

app = FastAPI(title="Property Service", version="1.0.0")

app.include_router(properties.router, prefix="/api/v1/properties", tags=["properties"])
app.include_router(units.router, prefix="/api/v1/units", tags=["units"])

# Импортируем модели для Alembic (после создания app, чтобы избежать циклических импортов)
from app.models.property import Property, Unit  # noqa: F401

@app.get("/health")
def health():
    return {"status": "ok"}
