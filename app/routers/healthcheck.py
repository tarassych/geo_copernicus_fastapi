from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.config import Settings, get_settings
import os

router = APIRouter()


@router.get("/healthcheck")
async def healthcheck(settings: Settings = Depends(get_settings)):
    """
    Health check endpoint to verify API accessibility and environment configuration.
    
    Returns:
    - status: Service health status
    - environment: Configuration from environment variables
    - api_key_configured: Whether TOPO_API_KEY is set
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "service": "Copernicus DEM FastAPI",
            "environment": {
                "target_dir": settings.target_dir,
                "log_dir": settings.log_dir,
                "port": os.getenv("PORT", "8000")
            },
            "api_key_configured": bool(settings.topo_api_key and settings.topo_api_key != "your_api_key_here"),
            "endpoints": {
                "docs": "/docs",
                "buildcache": "/buildcache",
                "elevation_point": "/elevation/point",
                "elevation_check": "/elevation/check",
                "elevation_difference": "/elevation/difference"
            }
        }
    )

