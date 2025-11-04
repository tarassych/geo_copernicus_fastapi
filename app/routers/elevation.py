from fastapi import APIRouter, Depends, HTTPException, Query
from app.config import Settings, get_settings
from app.models.elevation import (
    PointElevationRequest,
    PointElevationResponse,
    ElevationDifferenceRequest,
    ElevationDifferenceResponse,
    PointData
)
from app.services.elevation_service import ElevationService
from app.services.elevation_logger import ElevationLogger
from geopy.distance import geodesic
import math
import time

router = APIRouter()


@router.get("/elevation/point", response_model=PointElevationResponse)
async def get_point_elevation(
    latitude: float = Query(
        ...,
        description="Latitude in decimal degrees",
        ge=-90,
        le=90,
        example=50.7096667
    ),
    longitude: float = Query(
        ...,
        description="Longitude in decimal degrees",
        ge=-180,
        le=180,
        example=26.2353500
    ),
    resolution: str = Query(
        default="GLO-30",
        description="DEM resolution: GLO-30 (30m) or GLO-90 (90m)",
        pattern="^(GLO-30|GLO-90)$"
    ),
    settings: Settings = Depends(get_settings)
):
    """
    Get elevation for a specific point from cached Copernicus DEM tiles.
    
    This endpoint:
    1. Validates the coordinates
    2. Determines which tile contains the point
    3. Checks if the tile is cached
    4. Reads the elevation value from the GeoTIFF
    5. Returns the elevation in meters
    
    **Coordinate Requirements:**
    - Latitude: -90 to 90 degrees (decimal)
    - Longitude: -180 to 180 degrees (decimal)
    
    **Resolution Options:**
    - GLO-30: 30 meter resolution (default)
    - GLO-90: 90 meter resolution
    
    **Note:** The tile containing the requested point must be cached first.
    Use the `/buildcache` endpoint to download tiles for your area of interest.
    
    **Returns:**
    - Elevation value in meters above sea level
    - Tile information and data source
    - Error message if tile is not cached or point is invalid
    
    **Example:**
    ```
    GET /elevation/point?latitude=50.7096667&longitude=26.2353500&resolution=GLO-30
    ```
    """
    start_time = time.time()
    
    try:
        # Validate coordinates using Pydantic model
        point = PointElevationRequest(
            latitude=latitude,
            longitude=longitude
        )
        
        # Create elevation service
        elevation_service = ElevationService(settings.target_dir)
        
        # Get elevation
        elevation, tile_key, error = elevation_service.get_elevation(
            point.latitude,
            point.longitude,
            resolution
        )
        
        # Prepare response
        if error:
            response = PointElevationResponse(
                latitude=point.latitude,
                longitude=point.longitude,
                elevation_meters=None,
                resolution=resolution,
                tile_used=tile_key,
                status="error",
                message=error
            )
        elif elevation is None:
            response = PointElevationResponse(
                latitude=point.latitude,
                longitude=point.longitude,
                elevation_meters=None,
                resolution=resolution,
                tile_used=tile_key,
                status="no_data",
                message="No elevation data available at this location (possibly water or missing data)"
            )
        else:
            response = PointElevationResponse(
                latitude=point.latitude,
                longitude=point.longitude,
                elevation_meters=round(elevation, 2),
                resolution=resolution,
                tile_used=tile_key,
                status="success",
                message=None
            )
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Log the query
        logger = ElevationLogger(settings.log_dir)
        await logger.log_point_query(
            input_params={
                "latitude": point.latitude,
                "longitude": point.longitude,
                "resolution": resolution
            },
            result=response.dict(),
            execution_time=execution_time
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/elevation/check", response_model=dict)
async def check_tile_availability(
    latitude: float = Query(
        ...,
        description="Latitude in decimal degrees",
        ge=-90,
        le=90,
        example=50.7096667
    ),
    longitude: float = Query(
        ...,
        description="Longitude in decimal degrees",
        ge=-180,
        le=180,
        example=26.2353500
    ),
    resolution: str = Query(
        default="GLO-30",
        description="DEM resolution",
        pattern="^(GLO-30|GLO-90)$"
    ),
    settings: Settings = Depends(get_settings)
):
    """
    Check if a tile is available in cache for the given coordinates.
    
    This is a helper endpoint to check tile availability before querying elevation.
    
    **Returns:**
    - available: Boolean indicating if tile is cached
    - tile_key: The tile identifier (e.g., N50E026)
    - message: Information message
    """
    start_time = time.time()
    
    try:
        from app.services.tile_utils import format_tile_key
        import math
        
        tile_lat = int(math.floor(latitude))
        tile_lon = int(math.floor(longitude))
        tile_key = format_tile_key(tile_lat, tile_lon)
        
        elevation_service = ElevationService(settings.target_dir)
        is_available = elevation_service.check_tile_availability(
            latitude,
            longitude,
            resolution
        )
        
        if is_available:
            message = f"Tile {tile_key} is available in cache"
        else:
            message = f"Tile {tile_key} is not cached. Use /buildcache to download it."
        
        result = {
            "available": is_available,
            "tile_key": tile_key,
            "resolution": resolution,
            "message": message
        }
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Log the query
        logger = ElevationLogger(settings.log_dir)
        await logger.log_check_query(
            input_params={
                "latitude": latitude,
                "longitude": longitude,
                "resolution": resolution
            },
            result=result,
            execution_time=execution_time
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking tile availability: {str(e)}"
        )


@router.get("/elevation/difference", response_model=ElevationDifferenceResponse)
async def get_elevation_difference(
    point1_latitude: float = Query(
        ...,
        description="Latitude of first point in decimal degrees",
        ge=-90,
        le=90,
        example=50.7096667
    ),
    point1_longitude: float = Query(
        ...,
        description="Longitude of first point in decimal degrees",
        ge=-180,
        le=180,
        example=26.2353500
    ),
    point2_latitude: float = Query(
        ...,
        description="Latitude of second point in decimal degrees",
        ge=-90,
        le=90,
        example=50.597127
    ),
    point2_longitude: float = Query(
        ...,
        description="Longitude of second point in decimal degrees",
        ge=-180,
        le=180,
        example=26.147292
    ),
    resolution: str = Query(
        default="GLO-30",
        description="DEM resolution: GLO-30 (30m) or GLO-90 (90m)",
        pattern="^(GLO-30|GLO-90)$"
    ),
    settings: Settings = Depends(get_settings)
):
    """
    Calculate elevation difference between two points.
    
    This endpoint:
    1. Queries elevation for both points
    2. Calculates the vertical difference (elevation)
    3. Calculates the horizontal distance (geodesic)
    4. Computes slope angle and percentage
    
    **Parameters:**
    - point1: First reference point (from)
    - point2: Second point (to)
    
    **Returns:**
    - Elevation for both points
    - Elevation difference (point2 - point1)
      - Positive: point2 is higher than point1
      - Negative: point2 is lower than point1
    - Horizontal distance between points (meters)
    - Slope angle (degrees)
    - Slope percentage (rise/run * 100)
    
    **Note:** Both tiles must be cached. Use `/buildcache` first if needed.
    
    **Example:**
    ```
    GET /elevation/difference?point1_latitude=50.7096667&point1_longitude=26.2353500
                              &point2_latitude=50.597127&point2_longitude=26.147292
    ```
    
    **Use Cases:**
    - Terrain analysis between two locations
    - Hiking trail difficulty assessment
    - Road grade calculation
    - Viewshed analysis
    """
    start_time = time.time()
    
    try:
        # Validate coordinates
        request = ElevationDifferenceRequest(
            point1_latitude=point1_latitude,
            point1_longitude=point1_longitude,
            point2_latitude=point2_latitude,
            point2_longitude=point2_longitude
        )
        
        # Create elevation service
        elevation_service = ElevationService(settings.target_dir)
        
        # Get elevation for point 1
        elev1, tile1, error1 = elevation_service.get_elevation(
            request.point1_latitude,
            request.point1_longitude,
            resolution
        )
        
        # Get elevation for point 2
        elev2, tile2, error2 = elevation_service.get_elevation(
            request.point2_latitude,
            request.point2_longitude,
            resolution
        )
        
        # Check for errors
        if error1 or error2:
            errors = []
            if error1:
                errors.append(f"Point 1: {error1}")
            if error2:
                errors.append(f"Point 2: {error2}")
            
            response = ElevationDifferenceResponse(
                point1=PointData(
                    latitude=request.point1_latitude,
                    longitude=request.point1_longitude,
                    elevation_meters=elev1,
                    tile_used=tile1
                ),
                point2=PointData(
                    latitude=request.point2_latitude,
                    longitude=request.point2_longitude,
                    elevation_meters=elev2,
                    tile_used=tile2
                ),
                elevation_difference_meters=None,
                horizontal_distance_meters=None,
                slope_degrees=None,
                slope_percentage=None,
                resolution=resolution,
                status="error",
                message="; ".join(errors)
            )
            
            # Log error response
            execution_time = time.time() - start_time
            logger = ElevationLogger(settings.log_dir)
            await logger.log_difference_query(
                input_params={
                    "point1_latitude": request.point1_latitude,
                    "point1_longitude": request.point1_longitude,
                    "point2_latitude": request.point2_latitude,
                    "point2_longitude": request.point2_longitude,
                    "resolution": resolution
                },
                result=response.dict(),
                execution_time=execution_time
            )
            return response
        
        # Check if both elevations are available
        if elev1 is None or elev2 is None:
            missing = []
            if elev1 is None:
                missing.append("point 1")
            if elev2 is None:
                missing.append("point 2")
            
            response = ElevationDifferenceResponse(
                point1=PointData(
                    latitude=request.point1_latitude,
                    longitude=request.point1_longitude,
                    elevation_meters=elev1,
                    tile_used=tile1
                ),
                point2=PointData(
                    latitude=request.point2_latitude,
                    longitude=request.point2_longitude,
                    elevation_meters=elev2,
                    tile_used=tile2
                ),
                elevation_difference_meters=None,
                horizontal_distance_meters=None,
                slope_degrees=None,
                slope_percentage=None,
                resolution=resolution,
                status="no_data",
                message=f"No elevation data available for {' and '.join(missing)}"
            )
            
            # Log no_data response
            execution_time = time.time() - start_time
            logger = ElevationLogger(settings.log_dir)
            await logger.log_difference_query(
                input_params={
                    "point1_latitude": request.point1_latitude,
                    "point1_longitude": request.point1_longitude,
                    "point2_latitude": request.point2_latitude,
                    "point2_longitude": request.point2_longitude,
                    "resolution": resolution
                },
                result=response.dict(),
                execution_time=execution_time
            )
            return response
        
        # Calculate elevation difference (point2 - point1)
        elevation_diff = elev2 - elev1
        
        # Calculate horizontal distance using geodesic (great circle distance)
        horizontal_distance = geodesic(
            (request.point1_latitude, request.point1_longitude),
            (request.point2_latitude, request.point2_longitude)
        ).meters
        
        # Calculate slope
        slope_degrees = None
        slope_percentage = None
        slope_radians = None
        
        if horizontal_distance > 0:
            # Slope angle in degrees
            slope_radians = math.atan(abs(elevation_diff) / horizontal_distance)
            slope_degrees = math.degrees(slope_radians)
            
            # Slope percentage (rise/run * 100)
            slope_percentage = (abs(elevation_diff) / horizontal_distance) * 100
        
        response = ElevationDifferenceResponse(
            point1=PointData(
                latitude=request.point1_latitude,
                longitude=request.point1_longitude,
                elevation_meters=round(elev1, 2),
                tile_used=tile1
            ),
            point2=PointData(
                latitude=request.point2_latitude,
                longitude=request.point2_longitude,
                elevation_meters=round(elev2, 2),
                tile_used=tile2
            ),
            elevation_difference_meters=round(elevation_diff, 2),
            horizontal_distance_meters=round(horizontal_distance, 2),
            slope_degrees=round(slope_degrees, 2) if slope_degrees is not None else None,
            slope_percentage=round(slope_percentage, 2) if slope_percentage is not None else None,
            resolution=resolution,
            status="success",
            message=None
        )
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Log the query with all calculations
        logger = ElevationLogger(settings.log_dir)
        await logger.log_difference_query(
            input_params={
                "point1_latitude": request.point1_latitude,
                "point1_longitude": request.point1_longitude,
                "point2_latitude": request.point2_latitude,
                "point2_longitude": request.point2_longitude,
                "resolution": resolution
            },
            result=response.dict(),
            execution_time=execution_time,
            calculations={
                "geodesic_distance": {
                    "point1": (request.point1_latitude, request.point1_longitude),
                    "point2": (request.point2_latitude, request.point2_longitude),
                    "distance_meters": round(horizontal_distance, 2)
                },
                "elevation_data": {
                    "point1_raw": elev1,
                    "point2_raw": elev2,
                    "difference_raw": elevation_diff
                },
                "slope_formulas": {
                    "rise": abs(elevation_diff),
                    "run": horizontal_distance,
                    "angle_radians": slope_radians if horizontal_distance > 0 else None
                }
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

