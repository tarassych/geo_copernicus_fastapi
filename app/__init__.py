from fastapi import FastAPI
from app.routers import healthcheck, buildcache, elevation


def create_app() -> FastAPI:
    """
    Application factory for creating FastAPI instance
    """
    app = FastAPI(
        title="Copernicus FastAPI",
        description="FastAPI application for Copernicus DEM data",
        version="1.0.0"
    )

    # Include routers
    app.include_router(healthcheck.router, tags=["Health"])
    app.include_router(buildcache.router, tags=["Cache"])
    app.include_router(elevation.router, tags=["Elevation"])

    return app

