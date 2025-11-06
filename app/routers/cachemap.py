from fastapi import APIRouter, Depends, HTTPException, Query
from app.config import Settings, get_settings
from app.models.cachemap import CacheMapParams, CacheMapResponse, SquareResult
from app.models.buildcache import DEMResolution
from app.services.grid_splitter import GridSplitter
from app.services.tile_utils import normalize_aoi, compute_tile_keys
from app.services.opentopography import OpenTopographyService
from typing import Optional
import time
import asyncio
from datetime import datetime
from pathlib import Path
import json

router = APIRouter()


@router.get("/cachemap", response_model=CacheMapResponse)
async def cache_map(
    min_lat: float = Query(
        ...,
        description="Southern latitude of bounding box (decimal degrees)",
        ge=-90,
        le=90,
        example=48.0
    ),
    max_lat: float = Query(
        ...,
        description="Northern latitude of bounding box (decimal degrees)",
        ge=-90,
        le=90,
        example=52.0
    ),
    min_lon: float = Query(
        ...,
        description="Western longitude of bounding box (decimal degrees)",
        ge=-180,
        le=180,
        example=23.0
    ),
    max_lon: float = Query(
        ...,
        description="Eastern longitude of bounding box (decimal degrees)",
        ge=-180,
        le=180,
        example=27.0
    ),
    resolution: DEMResolution = Query(
        default=DEMResolution.GLO_30,
        description="DEM resolution: GLO-30 (30m) or GLO-90 (90m)"
    ),
    buffer_km: Optional[float] = Query(
        default=None,
        description="Extra margin around each square in kilometers",
        ge=0,
        example=5
    ),
    force_update: bool = Query(
        default=False,
        description="Redownload files even if they already exist"
    ),
    settings: Settings = Depends(get_settings)
):
    """
    Build Copernicus DEM cache for a large area by splitting it into 100km squares.
    
    This endpoint:
    1. Validates the input bounding box
    2. Splits the area into approximately 100km × 100km squares
    3. Processes each square through the buildcache logic:
       - Normalizes the AOI and applies buffer
       - Computes required 1×1° tiles
       - Downloads tiles from OpenTopography API
       - Checks cache before downloading (unless force_update=true)
       - Builds/refreshes GDAL VRT mosaic
    4. Returns a summary of all processed squares
    
    **Use Case:**
    When you need to cache DEM data for an area larger than 100km on any side,
    this endpoint automatically splits it into manageable chunks and processes each one.
    
    **Parameters:**
    - min_lat, max_lat, min_lon, max_lon: Define the total bounding box
    - resolution: GLO-30 (30m) or GLO-90 (90m)
    - buffer_km: Optional buffer added to EACH square (not the total area)
    - force_update: Force redownload for all squares
    
    **Returns:**
    - Grid information (number of squares, dimensions)
    - List of all squares with their coordinates
    - Processing results for each square
    - Overall summary and execution time
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
        params = CacheMapParams(
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            resolution=resolution,
            buffer_km=buffer_km,
            force_update=force_update
        )
        
        # Initialize grid splitter
        grid_splitter = GridSplitter(square_size_km=100.0)
        
        # Calculate total area dimensions
        total_ns_km, total_ew_km = grid_splitter.calculate_total_area(
            params.min_lat, params.max_lat, params.min_lon, params.max_lon
        )
        
        # Split into grid squares
        squares = grid_splitter.split_into_grid(
            params.min_lat, params.max_lat, params.min_lon, params.max_lon
        )
        
        # Initialize OpenTopography service
        ot_service = OpenTopographyService(settings)
        
        # Process each square
        results = []
        total_downloaded = 0
        total_skipped = 0
        total_failed = 0
        
        for square in squares:
            square_start_time = time.time()
            
            try:
                # Normalize AOI for this square
                norm_min_lat, norm_max_lat, norm_min_lon, norm_max_lon = normalize_aoi(
                    square.min_lat,
                    square.max_lat,
                    square.min_lon,
                    square.max_lon,
                    params.buffer_km
                )
                
                # Compute required tiles for this square
                tile_keys = compute_tile_keys(
                    norm_min_lat,
                    norm_max_lat,
                    norm_min_lon,
                    norm_max_lon
                )
                
                # Download tiles
                download_summary = await ot_service.download_tiles(
                    tile_keys,
                    params.resolution.value,
                    params.force_update
                )
                
                # Build VRT mosaic for this square's tiles
                ot_service.build_vrt_mosaic(
                    params.resolution.value,
                    tile_keys
                )
                
                # Calculate execution time for this square
                square_execution_time = time.time() - square_start_time
                
                # Accumulate totals
                downloaded = len(download_summary['downloaded'])
                skipped = len(download_summary['skipped'])
                failed = len(download_summary['failed'])
                
                total_downloaded += downloaded
                total_skipped += skipped
                total_failed += failed
                
                # Create result for this square
                result = SquareResult(
                    square_id=square.square_id,
                    status="success",
                    tiles_downloaded=downloaded,
                    tiles_skipped=skipped,
                    tiles_failed=failed,
                    execution_time_seconds=round(square_execution_time, 2)
                )
                
                results.append(result)
                
            except Exception as e:
                # Record error for this square but continue with others
                square_execution_time = time.time() - square_start_time
                result = SquareResult(
                    square_id=square.square_id,
                    status="error",
                    tiles_downloaded=0,
                    tiles_skipped=0,
                    tiles_failed=0,
                    execution_time_seconds=round(square_execution_time, 2),
                    error=str(e)
                )
                results.append(result)
        
        # Calculate total execution time
        total_execution_time = time.time() - start_time
        
        # Create log file
        log_file = await _log_cachemap_summary(
            params=params,
            squares=squares,
            results=results,
            total_area=(total_ns_km, total_ew_km),
            execution_time=total_execution_time,
            settings=settings
        )
        
        # Prepare response
        total_area_info = {
            "north_south_km": round(total_ns_km, 2),
            "east_west_km": round(total_ew_km, 2)
        }
        
        grid_info = {
            "total_squares": len(squares),
            "square_size_target_km": 100.0,
            "rows": len(set(s.square_id.split('_')[1] for s in squares)),
            "columns": len(set(s.square_id.split('_')[2] for s in squares))
        }
        
        successful_squares = sum(1 for r in results if r.status == "success")
        failed_squares = sum(1 for r in results if r.status == "error")
        
        summary = {
            "successful_squares": successful_squares,
            "failed_squares": failed_squares,
            "total_tiles_downloaded": total_downloaded,
            "total_tiles_skipped": total_skipped,
            "total_tiles_failed": total_failed
        }
        
        return CacheMapResponse(
            status="success" if failed_squares == 0 else "partial_success",
            message=f"Processed {len(squares)} squares. "
                   f"{successful_squares} successful, {failed_squares} failed. "
                   f"Total: {total_downloaded} tiles downloaded, "
                   f"{total_skipped} skipped, {total_failed} failed.",
            total_area=total_area_info,
            grid_info=grid_info,
            squares=squares,
            results=results,
            summary=summary,
            execution_time_seconds=round(total_execution_time, 2),
            log_file=log_file
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


async def _log_cachemap_summary(
    params: CacheMapParams,
    squares: list,
    results: list,
    total_area: tuple,
    execution_time: float,
    settings: Settings
) -> str:
    """
    Log the cachemap operation summary to a JSON file.
    
    Args:
        params: CacheMapParams object
        squares: List of GridSquare objects
        results: List of SquareResult objects
        total_area: Tuple of (north_south_km, east_west_km)
        execution_time: Total execution time in seconds
        settings: Application settings
    
    Returns:
        Path to the log file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"cachemap_{timestamp}.json"
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": "/cachemap",
        "input_parameters": {
            "bounding_box": {
                "min_lat": params.min_lat,
                "max_lat": params.max_lat,
                "min_lon": params.min_lon,
                "max_lon": params.max_lon
            },
            "resolution": params.resolution.value,
            "buffer_km": params.buffer_km,
            "force_update": params.force_update
        },
        "total_area": {
            "north_south_km": round(total_area[0], 2),
            "east_west_km": round(total_area[1], 2)
        },
        "grid_info": {
            "total_squares": len(squares),
            "square_size_target_km": 100.0
        },
        "squares": [
            {
                "square_id": square.square_id,
                "min_lat": square.min_lat,
                "max_lat": square.max_lat,
                "min_lon": square.min_lon,
                "max_lon": square.max_lon,
                "center_lat": square.center_lat,
                "center_lon": square.center_lon
            }
            for square in squares
        ],
        "results": [
            {
                "square_id": result.square_id,
                "status": result.status,
                "tiles_downloaded": result.tiles_downloaded,
                "tiles_skipped": result.tiles_skipped,
                "tiles_failed": result.tiles_failed,
                "execution_time_seconds": result.execution_time_seconds,
                "error": result.error
            }
            for result in results
        ],
        "summary": {
            "successful_squares": sum(1 for r in results if r.status == "success"),
            "failed_squares": sum(1 for r in results if r.status == "error"),
            "total_tiles_downloaded": sum(r.tiles_downloaded for r in results),
            "total_tiles_skipped": sum(r.tiles_skipped for r in results),
            "total_tiles_failed": sum(r.tiles_failed for r in results)
        },
        "execution_time_seconds": round(execution_time, 2)
    }
    
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    return str(log_file)

