from fastapi import FastAPI
from api.routes.jobs import router as jobs_router

app = FastAPI(title="UNTANGLE API")
app.include_router(jobs_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "project": "UNTANGLE"}
