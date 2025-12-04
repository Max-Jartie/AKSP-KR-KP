from fastapi import FastAPI
from app.api.v1 import leases, payments

app = FastAPI(title="Leasing Service", version="1.0.0")

app.include_router(leases.router, prefix="/api/v1/leases", tags=["leases"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])


@app.get("/health")
def health():
    return {"status": "ok"}