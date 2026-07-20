from fastapi import FastAPI

app = FastAPI(title="Address Parser API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
