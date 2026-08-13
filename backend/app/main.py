from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.auth import router as auth_router
from app.api.routers.enrich import router as enrich_router
from app.api.routers.parse import router as parse_router
from app.core.config import get_settings

settings = get_settings()

# Disable interactive docs in production to reduce attack surface
_docs_url = None if settings.app_env == "production" else "/docs"
_redoc_url = None if settings.app_env == "production" else "/redoc"
_openapi_url = None if settings.app_env == "production" else "/openapi.json"

app = FastAPI(
    title="Address Parser API",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)
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
