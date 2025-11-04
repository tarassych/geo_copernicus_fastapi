from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from enum import Enum
from geopy.distance import geodesic


class DEMResolution(str, Enum):
    """DEM resolution options"""
    GLO_30 = "GLO-30"
    GLO_90 = "GLO-90"


class BuildCacheParams(BaseModel):
    """
    Parameters for building Copernicus DEM cache
    """
    min_lat: float = Field(
        ...,
        description="Southern latitude of bounding box (decimal degrees)",
        ge=-90,
        le=90,
        examples=[48.5]
    )
    max_lat: float = Field(
        ...,
        description="Northern latitude of bounding box (decimal degrees)",
        ge=-90,
        le=90,
        examples=[50.2]
    )
    min_lon: float = Field(
        ...,
        description="Western longitude of bounding box (decimal degrees)",
        ge=-180,
        le=180,
        examples=[23.3]
    )
    max_lon: float = Field(
        ...,
        description="Eastern longitude of bounding box (decimal degrees)",
        ge=-180,
        le=180,
        examples=[25.1]
    )
    resolution: DEMResolution = Field(
        default=DEMResolution.GLO_30,
        description="DEM resolution: GLO-30 (30m) or GLO-90 (90m)"
    )
    buffer_km: Optional[float] = Field(
        default=None,
        description="Extra margin around bounding box in kilometers",
        ge=0,
        examples=[10]
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

    @model_validator(mode='after')
    def validate_bounding_box_size(self):
        """
        Ensure the bounding box is not larger than 100km on any side
        """
        # Calculate center longitude for more accurate east-west distance
        center_lon = (self.min_lon + self.max_lon) / 2
        center_lat = (self.min_lat + self.max_lat) / 2
        
        # Calculate north-south distance (latitude difference)
        north_south_distance = geodesic(
            (self.min_lat, center_lon),
            (self.max_lat, center_lon)
        ).kilometers
        
        # Calculate east-west distance (longitude difference)
        # Use center latitude for more accurate calculation
        east_west_distance = geodesic(
            (center_lat, self.min_lon),
            (center_lat, self.max_lon)
        ).kilometers
        
        max_distance = 100.0  # km
        
        if north_south_distance > max_distance:
            raise ValueError(
                f"Bounding box is too large: north-south distance is {north_south_distance:.2f} km, "
                f"maximum allowed is {max_distance} km"
            )
        
        if east_west_distance > max_distance:
            raise ValueError(
                f"Bounding box is too large: east-west distance is {east_west_distance:.2f} km, "
                f"maximum allowed is {max_distance} km"
            )
        
        return self


class BuildCacheResponse(BaseModel):
    """
    Response model for buildcache endpoint
    """
    status: str
    message: str
    parameters: dict
    distances: Optional[dict] = None
    tiles: Optional[dict] = None
    download_summary: Optional[dict] = None
    mosaic_path: Optional[str] = None
    log_file: Optional[str] = None
    execution_time_seconds: Optional[float] = None

