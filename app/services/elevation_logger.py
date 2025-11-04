"""
Logging service for elevation operations
"""
import json
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ElevationLogger:
    """
    Service for logging elevation queries and operations
    """
    
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    async def log_point_query(
        self,
        input_params: Dict[str, Any],
        result: Dict[str, Any],
        execution_time: float
    ) -> str:
        """
        Log a single point elevation query.
        
        Args:
            input_params: Input parameters (latitude, longitude, resolution)
            result: Query results (elevation, tile, status)
            execution_time: Time taken in seconds
        
        Returns:
            Path to log file
        """
        timestamp = datetime.utcnow()
        log_filename = f"elevation_point_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
        log_path = self.log_dir / log_filename
        
        log_data = {
            "operation": "elevation_point",
            "timestamp": timestamp.isoformat(),
            "execution_time_seconds": round(execution_time, 4),
            "input_parameters": input_params,
            "result": result,
            "middleware_calculations": {
                "tile_identification": {
                    "tile_lat": int(input_params["latitude"] // 1),
                    "tile_lon": int(input_params["longitude"] // 1),
                    "tile_used": result.get("tile_used")
                },
                "coordinate_validation": {
                    "latitude_valid": -90 <= input_params["latitude"] <= 90,
                    "longitude_valid": -180 <= input_params["longitude"] <= 180
                }
            }
        }
        
        async with aiofiles.open(log_path, 'w') as f:
            await f.write(json.dumps(log_data, indent=2))
        
        return str(log_path)
    
    async def log_difference_query(
        self,
        input_params: Dict[str, Any],
        result: Dict[str, Any],
        execution_time: float,
        calculations: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an elevation difference query between two points.
        
        Args:
            input_params: Input parameters (two coordinate pairs, resolution)
            result: Query results (elevations, difference, slope, etc.)
            execution_time: Time taken in seconds
            calculations: Intermediate calculation details
        
        Returns:
            Path to log file
        """
        timestamp = datetime.utcnow()
        log_filename = f"elevation_difference_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
        log_path = self.log_dir / log_filename
        
        log_data = {
            "operation": "elevation_difference",
            "timestamp": timestamp.isoformat(),
            "execution_time_seconds": round(execution_time, 4),
            "input_parameters": input_params,
            "result": result,
            "middleware_calculations": {
                "point1_tile": {
                    "tile_lat": int(input_params["point1_latitude"] // 1),
                    "tile_lon": int(input_params["point1_longitude"] // 1),
                    "tile_used": result.get("point1", {}).get("tile_used")
                },
                "point2_tile": {
                    "tile_lat": int(input_params["point2_latitude"] // 1),
                    "tile_lon": int(input_params["point2_longitude"] // 1),
                    "tile_used": result.get("point2", {}).get("tile_used")
                },
                "distance_calculation": {
                    "method": "geodesic",
                    "horizontal_distance_meters": result.get("horizontal_distance_meters")
                },
                "elevation_calculations": {
                    "point1_elevation": result.get("point1", {}).get("elevation_meters"),
                    "point2_elevation": result.get("point2", {}).get("elevation_meters"),
                    "difference": result.get("elevation_difference_meters"),
                    "direction": "ascending" if result.get("elevation_difference_meters", 0) > 0 else "descending" if result.get("elevation_difference_meters", 0) < 0 else "flat"
                },
                "slope_calculations": {
                    "angle_degrees": result.get("slope_degrees"),
                    "percentage": result.get("slope_percentage"),
                    "method": "atan(rise/run)"
                }
            }
        }
        
        if calculations:
            log_data["middleware_calculations"]["additional"] = calculations
        
        async with aiofiles.open(log_path, 'w') as f:
            await f.write(json.dumps(log_data, indent=2))
        
        return str(log_path)
    
    async def log_check_query(
        self,
        input_params: Dict[str, Any],
        result: Dict[str, Any],
        execution_time: float
    ) -> str:
        """
        Log a tile availability check query.
        
        Args:
            input_params: Input parameters (latitude, longitude, resolution)
            result: Check results (availability, tile_key)
            execution_time: Time taken in seconds
        
        Returns:
            Path to log file
        """
        timestamp = datetime.utcnow()
        log_filename = f"elevation_check_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
        log_path = self.log_dir / log_filename
        
        log_data = {
            "operation": "elevation_check",
            "timestamp": timestamp.isoformat(),
            "execution_time_seconds": round(execution_time, 4),
            "input_parameters": input_params,
            "result": result,
            "middleware_calculations": {
                "tile_identification": {
                    "tile_lat": int(input_params["latitude"] // 1),
                    "tile_lon": int(input_params["longitude"] // 1),
                    "tile_key": result.get("tile_key")
                },
                "cache_check": {
                    "available": result.get("available"),
                    "resolution": input_params.get("resolution")
                }
            }
        }
        
        async with aiofiles.open(log_path, 'w') as f:
            await f.write(json.dumps(log_data, indent=2))
        
        return str(log_path)

