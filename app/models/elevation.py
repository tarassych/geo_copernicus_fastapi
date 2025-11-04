from pydantic import BaseModel, Field, field_validator


class PointElevationRequest(BaseModel):
    """
    Request model for point elevation query
    """
    latitude: float = Field(
        ...,
        description="Latitude in decimal degrees",
        ge=-90,
        le=90,
        examples=[50.7096667]
    )
    longitude: float = Field(
        ...,
        description="Longitude in decimal degrees",
        ge=-180,
        le=180,
        examples=[26.2353500]
    )

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude is within valid range"""
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude is within valid range"""
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return v


class PointElevationResponse(BaseModel):
    """
    Response model for point elevation query
    """
    latitude: float
    longitude: float
    elevation_meters: float | None
    resolution: str
    tile_used: str | None
    data_source: str = "Copernicus DEM"
    status: str
    message: str | None = None


class ElevationDifferenceRequest(BaseModel):
    """
    Request model for elevation difference between two points
    """
    point1_latitude: float = Field(
        ...,
        description="Latitude of first point in decimal degrees",
        ge=-90,
        le=90,
        examples=[50.7096667]
    )
    point1_longitude: float = Field(
        ...,
        description="Longitude of first point in decimal degrees",
        ge=-180,
        le=180,
        examples=[26.2353500]
    )
    point2_latitude: float = Field(
        ...,
        description="Latitude of second point in decimal degrees",
        ge=-90,
        le=90,
        examples=[50.597127]
    )
    point2_longitude: float = Field(
        ...,
        description="Longitude of second point in decimal degrees",
        ge=-180,
        le=180,
        examples=[26.147292]
    )


class PointData(BaseModel):
    """
    Elevation data for a single point
    """
    latitude: float
    longitude: float
    elevation_meters: float | None
    tile_used: str | None


class ElevationDifferenceResponse(BaseModel):
    """
    Response model for elevation difference query
    """
    point1: PointData
    point2: PointData
    elevation_difference_meters: float | None = Field(
        None,
        description="Elevation difference (point2 - point1). Positive means point2 is higher."
    )
    horizontal_distance_meters: float | None = Field(
        None,
        description="Horizontal distance between the two points"
    )
    slope_degrees: float | None = Field(
        None,
        description="Slope angle in degrees"
    )
    slope_percentage: float | None = Field(
        None,
        description="Slope as percentage (rise/run * 100)"
    )
    resolution: str
    data_source: str = "Copernicus DEM"
    status: str
    message: str | None = None

