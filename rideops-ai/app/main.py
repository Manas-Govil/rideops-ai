import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import api_router
from app.config import settings
from app.database.connection import test_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("RideOps_App")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan setup and teardown."""
    logger.info("Initializing RideOps AI Application...")
    is_connected = test_connection()
    if not is_connected:
        logger.error("WARNING: PostgreSQL connection failed during startup.")
    else:
        logger.info("PostgreSQL database connection verified.")
    yield
    logger.info("Shutting down RideOps AI Application...")


app = FastAPI(
    title="RideOps AI - Governed Mobility Analytics API",
    description="Multi-agent NYC taxi mobility analytics platform with strict SQL guardrails and audit logging.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix="/api")


@app.get("/", summary="Root Endpoint")
def root():
    return {
        "project": "RideOps AI",
        "description": "Governed Multi-Agent NYC Mobility Analytics System",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
