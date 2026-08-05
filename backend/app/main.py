from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.auth import router as auth_router
from app.api.routers.enrich import router as enrich_router
from app.api.routers.parse import router as parse_router
from app.core.config import get_settings

app = FastAPI(title="Address Parser API")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.include_router(auth_router)
app.include_router(parse_router)
app.include_router(enrich_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
