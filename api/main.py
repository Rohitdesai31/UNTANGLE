from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.jobs import router as jobs_router
from api.routes.upload import router as upload_router
from api.routes.results import router as results_router
from api.routes.analysis import router as analysis_router
from api.routes.corrections import router as corrections_router

app = FastAPI(
    title="UNTANGLE API",
    description="AI-based P&ID to simplified process sketch platform.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    jobs_router,
    prefix="/api",
)

app.include_router(
    upload_router,
    prefix="/api",
)

app.include_router(
    results_router,
    prefix="/api",
)

app.include_router(
    analysis_router,
    prefix="/api",
)

app.include_router(corrections_router, prefix="/api")

@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "project": "UNTANGLE",
    }