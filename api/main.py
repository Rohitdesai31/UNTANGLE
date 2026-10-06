from fastapi import FastAPI

from api.routes.jobs import router as jobs_router
from api.routes.upload import router as upload_router


app = FastAPI(
    title="UNTANGLE API",
    description="AI-based P&ID to simplified process sketch platform.",
    version="1.0.0",
)


app.include_router(
    jobs_router,
    prefix="/api",
)

app.include_router(
    upload_router,
    prefix="/api",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "project": "UNTANGLE",
    }