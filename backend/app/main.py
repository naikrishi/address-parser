from fastapi import FastAPI

from app.api.routers.enrich import router as enrich_router
from app.api.routers.parse import router as parse_router

app = FastAPI(title="Address Parser API")

app.include_router(parse_router)
app.include_router(enrich_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
