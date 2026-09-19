from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.expenditures import router as expenditures_router
from api.routers.ingest import router as ingest_router
from api.routers.mappings import router as mappings_router
from api.routers.overview import router as overview_router
from pipeline.db import ROOT, init_database


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_database()
    yield


app = FastAPI(
    title="Health expenditure review",
    description="Harmonised multi-country expenditure review prototype",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview_router)
app.include_router(expenditures_router)
app.include_router(mappings_router)
app.include_router(ingest_router)

FRONTEND_DIR = ROOT / "web" / "dist"
if FRONTEND_DIR.exists():
    app.frontend("/", directory=str(FRONTEND_DIR))


@app.get("/api/health")
def health() -> dict[str, str]:
    init_database()
    return {"status": "ok"}
