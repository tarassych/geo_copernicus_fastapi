from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from app.models.buildcache import DEMResolution


class CacheMapParams(BaseModel):
    """
    Parameters for building cache map from large area split into 100km squares
    """
    min_lat: float = Field(
        ...,
        description="Southern latitude of bounding box (decimal degrees)",
        ge=-90,
        le=90,
        examples=[48.0]
    )
    max_lat: float = Field(
        ...,
        description="Northern latitude of bounding box (decimal degrees)",
        ge=-90,
        le=90,
        examples=[52.0]
    )
    min_lon: float = Field(
        ...,
        description="Western longitude of bounding box (decimal degrees)",
        ge=-180,
        le=180,
        examples=[23.0]
    )
    max_lon: float = Field(
        ...,
        description="Eastern longitude of bounding box (decimal degrees)",
        ge=-180,
        le=180,
        examples=[27.0]
    )
    resolution: DEMResolution = Field(
        default=DEMResolution.GLO_30,
        description="DEM resolution: GLO-30 (30m) or GLO-90 (90m)"
    )
    buffer_km: Optional[float] = Field(
        default=None,
        description="Extra margin around each square in kilometers",
        ge=0,
        examples=[5]
    )
    force_update: bool = Field(
        default=False,
        description="Redownload files even if they already exist"
    )

    @field_validator("max_lat")
    @classmethod
    def validate_max_lat(cls, v, info):
        """Ensure max_lat is greater than min_lat"""
        if "min_lat" in info.data and v <= info.data["min_lat"]:
            raise ValueError("max_lat must be greater than min_lat")
        return v

    @field_validator("max_lon")
    @classmethod
    def validate_max_lon(cls, v, info):
        """Ensure max_lon is greater than min_lon"""
        if "min_lon" in info.data and v <= info.data["min_lon"]:
            raise ValueError("max_lon must be greater than min_lon")
        return v


class GridSquare(BaseModel):
    """Represents a single 100km square in the grid"""
    square_id: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    center_lat: float
    center_lon: float


class SquareResult(BaseModel):
    """Result of processing a single square"""
    square_id: str
    status: str
    tiles_downloaded: int
    tiles_skipped: int
    tiles_failed: int
    execution_time_seconds: float
    error: Optional[str] = None


class CacheMapResponse(BaseModel):
    """
    Response model for cachemap endpoint
    """
    status: str
    message: str
    total_area: Dict[str, float]
    grid_info: Dict[str, Any]
    squares: List[GridSquare]
    results: List[SquareResult]
    summary: Dict[str, Any]
    execution_time_seconds: float
    log_file: Optional[str] = None

