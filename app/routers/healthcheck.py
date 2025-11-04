from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.config import Settings, get_settings

router = APIRouter()


@router.get("/healthcheck")
async def healthcheck(settings: Settings = Depends(get_settings)):
    """
    Health check endpoint to verify API accessibility
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "target_dir": settings.target_dir
        }
    )

