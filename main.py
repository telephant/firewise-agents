import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes import runway_router, import_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title="Firewise Agents",
    description="AI-powered financial agents for Firewise",
    version="1.0.0",
)


# CORS middleware (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to firewise-api domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routes
app.include_router(runway_router, prefix="/runway", tags=["runway"])
app.include_router(import_router, prefix="/import", tags=["import"])


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {
        "status": "ok",
        "service": "firewise-agents",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "firewise-agents",
        "version": "1.0.0",
        "endpoints": {
            "runway": "POST /runway",
            "import": "POST /import",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
