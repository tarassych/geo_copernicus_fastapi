from fastapi import APIRouter, Depends, HTTPException, Query
from app.config import Settings, get_settings
from app.models.buildcache import BuildCacheParams, BuildCacheResponse, DEMResolution
from app.services.tile_utils import normalize_aoi, compute_tile_keys
from app.services.opentopography import OpenTopographyService
from typing import Optional
from geopy.distance import geodesic
import time

router = APIRouter()


@router.get("/buildcache", response_model=BuildCacheResponse)
async def build_cache(
    min_lat: float = Query(
        ...,
        description="Southern latitude of bounding box (decimal degrees)",
        ge=-90,
        le=90,
        example=48.5
    ),
    max_lat: float = Query(
        ...,
        description="Northern latitude of bounding box (decimal degrees)",
        ge=-90,
        le=90,
        example=50.2
    ),
    min_lon: float = Query(
        ...,
        description="Western longitude of bounding box (decimal degrees)",
        ge=-180,
        le=180,
        example=23.3
    ),
    max_lon: float = Query(
        ...,
        description="Eastern longitude of bounding box (decimal degrees)",
        ge=-180,
        le=180,
        example=25.1
    ),
    resolution: DEMResolution = Query(
        default=DEMResolution.GLO_30,
        description="DEM resolution: GLO-30 (30m) or GLO-90 (90m)"
    ),
    buffer_km: Optional[float] = Query(
        default=None,
        description="Extra margin around bounding box in kilometers",
        ge=0,
        example=10
    ),
    force_update: bool = Query(
        default=False,
        description="Redownload files even if they already exist"
    ),
    settings: Settings = Depends(get_settings)
):
    """
    Build Copernicus DEM cache for a specified bounding box.
    
    This endpoint:
    1. Validates and normalizes the AOI (Area of Interest)
    2. Applies optional buffer and clamps to valid lat/lon
    3. Computes required 1×1° tiles
    4. Downloads tiles from OpenTopography API
    5. Checks cache before downloading (unless force_update=true)
    6. Builds/refreshes GDAL VRT mosaic
    7. Logs operation summary
    
    **Bounding Box Requirements:**
    - max_lat must be greater than min_lat
    - max_lon must be greater than min_lon
    - Latitude range: -90 to 90 degrees
    - Longitude range: -180 to 180 degrees
    - Maximum size: 100 km on each side (north-south and east-west)
    
    **Resolution Options:**
    - GLO-30: 30 meter resolution (default)
    - GLO-90: 90 meter resolution
    
    **Optional Parameters:**
    - buffer_km: Adds extra margin (in km) to all sides before downloading
    - force_update: Forces redownload even if files exist in cache
    
    **Returns:**
    - Operation summary including downloaded/skipped/failed tiles
    - Paths to cached data and mosaic
    - Execution time and log file location
    """
    start_time = time.time()
    
    try:
        # Validate API key
        if not settings.topo_api_key or settings.topo_api_key == "your_api_key_here":
            raise HTTPException(
                status_code=500,
                detail="OpenTopography API key not configured. Please set TOPO_API_KEY in .env file"
            )
        
        # Validate parameters using Pydantic model
        params = BuildCacheParams(
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            resolution=resolution,
            buffer_km=buffer_km,
            force_update=force_update
        )
        
        # Additional validation
        if max_lat <= min_lat:
            raise HTTPException(
                status_code=400,
                detail="max_lat must be greater than min_lat"
            )
        
        if max_lon <= min_lon:
            raise HTTPException(
                status_code=400,
                detail="max_lon must be greater than min_lon"
            )
        
        # Calculate distances for response
        center_lon = (params.min_lon + params.max_lon) / 2
        center_lat = (params.min_lat + params.max_lat) / 2
        
        north_south_distance = geodesic(
            (params.min_lat, center_lon),
            (params.max_lat, center_lon)
        ).kilometers
        
        east_west_distance = geodesic(
            (center_lat, params.min_lon),
            (center_lat, params.max_lon)
        ).kilometers
        
        # Step 1: Normalize AOI and apply buffer
        norm_min_lat, norm_max_lat, norm_min_lon, norm_max_lon = normalize_aoi(
            params.min_lat,
            params.max_lat,
            params.min_lon,
            params.max_lon,
            params.buffer_km
        )
        
        # Step 2: Compute required tiles
        tile_keys = compute_tile_keys(
            norm_min_lat,
            norm_max_lat,
            norm_min_lon,
            norm_max_lon
        )
        
        # Step 3: Download tiles using OpenTopography service
        ot_service = OpenTopographyService(settings)
        download_summary = await ot_service.download_tiles(
            tile_keys,
            params.resolution.value,
            params.force_update
        )
        
        # Step 4: Build VRT mosaic
        mosaic_path = ot_service.build_vrt_mosaic(
            params.resolution.value,
            tile_keys
        )
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Prepare input parameters for logging
        input_params = {
            "original_bbox": {
                "min_lat": params.min_lat,
                "max_lat": params.max_lat,
                "min_lon": params.min_lon,
                "max_lon": params.max_lon
            },
            "normalized_bbox": {
                "min_lat": norm_min_lat,
                "max_lat": norm_max_lat,
                "min_lon": norm_min_lon,
                "max_lon": norm_max_lon
            },
            "resolution": params.resolution.value,
            "buffer_km": params.buffer_km,
            "force_update": params.force_update
        }
        
        # Step 5: Log summary
        log_file = await ot_service.log_summary(
            input_params,
            download_summary,
            mosaic_path,
            execution_time
        )
        
        # Prepare response
        response_params = {
            "original_bounding_box": {
                "min_lat": params.min_lat,
                "max_lat": params.max_lat,
                "min_lon": params.min_lon,
                "max_lon": params.max_lon
            },
            "normalized_bounding_box": {
                "min_lat": norm_min_lat,
                "max_lat": norm_max_lat,
                "min_lon": norm_min_lon,
                "max_lon": norm_max_lon
            },
            "resolution": params.resolution.value,
            "buffer_km": params.buffer_km,
            "force_update": params.force_update,
            "target_dir": settings.target_dir
        }
        
        distances_info = {
            "north_south_km": round(north_south_distance, 2),
            "east_west_km": round(east_west_distance, 2),
            "max_allowed_km": 100.0
        }
        
        tiles_info = {
            "required_tiles": tile_keys,
            "tile_count": len(tile_keys)
        }
        
        return BuildCacheResponse(
            status="success",
            message=f"Cache build completed. Downloaded {len(download_summary['downloaded'])} tiles, "
                   f"skipped {len(download_summary['skipped'])} existing tiles, "
                   f"{len(download_summary['failed'])} failed.",
            parameters=response_params,
            distances=distances_info,
            tiles=tiles_info,
            download_summary=download_summary,
            mosaic_path=mosaic_path,
            log_file=log_file,
            execution_time_seconds=round(execution_time, 2)
        )
        
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

