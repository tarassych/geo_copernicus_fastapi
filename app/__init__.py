from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.routers import healthcheck, buildcache, cachemap, elevation


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
    app.include_router(cachemap.router, tags=["Cache"])
    app.include_router(elevation.router, tags=["Elevation"])

    # Mount static map application
    map_static_path = Path(__file__).parent.parent / "mapapp" / "out"
    if map_static_path.exists():
        # Mount static files for map application
        app.mount("/map", StaticFiles(directory=str(map_static_path), html=True), name="map")
        
        # Redirect /mapapp to /map/ for consistency
        @app.get("/mapapp")
        @app.head("/mapapp")
        async def redirect_to_map():
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/map/", status_code=301)
    
    return app

