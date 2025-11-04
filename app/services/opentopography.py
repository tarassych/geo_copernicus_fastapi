"""
OpenTopography API service for downloading Copernicus DEM tiles
"""
import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
import aiohttp
import aiofiles
from app.config import Settings


class OpenTopographyService:
    """
    Service for interacting with OpenTopography API to download Copernicus DEM data
    """
    
    BASE_URL = "https://portal.opentopography.org/API/globaldem"
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.topo_api_key
        self.target_dir = Path(settings.target_dir)
        self.log_dir = Path(settings.log_dir)
        
    async def download_tiles(
        self,
        tile_keys: List[str],
        resolution: str,
        force_update: bool = False
    ) -> Dict:
        """
        Download DEM tiles from OpenTopography.
        
        Args:
            tile_keys: List of tile keys (e.g., ['N49E024', 'N50E025'])
            resolution: DEM resolution ('GLO-30' or 'GLO-90')
            force_update: Whether to redownload existing files
        
        Returns:
            Dictionary with download summary
        """
        # Ensure directories exist
        self._ensure_directories(resolution)
        
        downloaded_tiles = []
        skipped_tiles = []
        failed_tiles = []
        total_bytes = 0
        
        # Map resolution to OpenTopography dataset
        dem_type = self._get_dem_type(resolution)
        
        # Process each tile
        async with aiohttp.ClientSession() as session:
            tasks = []
            for tile_key in tile_keys:
                task = self._download_single_tile(
                    session, tile_key, resolution, dem_type, force_update
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for tile_key, result in zip(tile_keys, results):
                if isinstance(result, Exception):
                    failed_tiles.append({
                        "tile": tile_key,
                        "error": str(result)
                    })
                elif result["status"] == "downloaded":
                    downloaded_tiles.append(tile_key)
                    total_bytes += result.get("bytes", 0)
                elif result["status"] == "skipped":
                    skipped_tiles.append(tile_key)
                elif result["status"] == "failed":
                    failed_tiles.append({
                        "tile": tile_key,
                        "error": result.get("error", "Unknown error")
                    })
        
        summary = {
            "downloaded": downloaded_tiles,
            "skipped": skipped_tiles,
            "failed": failed_tiles,
            "total_bytes": total_bytes,
            "total_tiles": len(tile_keys)
        }
        
        return summary
    
    async def _download_single_tile(
        self,
        session: aiohttp.ClientSession,
        tile_key: str,
        resolution: str,
        dem_type: str,
        force_update: bool
    ) -> Dict:
        """
        Download a single tile.
        
        Returns:
            Dictionary with status and metadata
        """
        # Parse tile key to get bounds
        from app.services.tile_utils import parse_tile_key
        lat, lon = parse_tile_key(tile_key)
        
        # Calculate bounds for the tile (1×1 degree)
        south = lat
        north = lat + 1
        west = lon
        east = lon + 1
        
        # Create tile directory
        tile_dir = self.target_dir / resolution / tile_key
        tile_dir.mkdir(parents=True, exist_ok=True)
        
        # Output file path
        output_file = tile_dir / f"{tile_key}.tif"
        
        # Check if file already exists
        if output_file.exists() and not force_update:
            return {
                "status": "skipped",
                "tile": tile_key,
                "reason": "already_exists"
            }
        
        # Build API request
        params = {
            "demtype": dem_type,
            "south": south,
            "north": north,
            "west": west,
            "east": east,
            "outputFormat": "GTiff",
            "API_Key": self.api_key
        }
        
        try:
            async with session.get(self.BASE_URL, params=params, timeout=300) as response:
                if response.status == 200:
                    # Download the file
                    content = await response.read()
                    
                    # Save to disk
                    async with aiofiles.open(output_file, 'wb') as f:
                        await f.write(content)
                    
                    return {
                        "status": "downloaded",
                        "tile": tile_key,
                        "bytes": len(content),
                        "path": str(output_file)
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "failed",
                        "tile": tile_key,
                        "error": f"HTTP {response.status}: {error_text[:200]}"
                    }
        except asyncio.TimeoutError:
            return {
                "status": "failed",
                "tile": tile_key,
                "error": "Request timeout"
            }
        except Exception as e:
            return {
                "status": "failed",
                "tile": tile_key,
                "error": str(e)
            }
    
    def _get_dem_type(self, resolution: str) -> str:
        """
        Map resolution to OpenTopography DEM type.
        """
        mapping = {
            "GLO-30": "COP30",  # Copernicus 30m
            "GLO-90": "COP90"   # Copernicus 90m
        }
        return mapping.get(resolution, "COP30")
    
    def _ensure_directories(self, resolution: str):
        """
        Ensure target and log directories exist.
        """
        # Create target directory
        target_path = self.target_dir / resolution
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def build_vrt_mosaic(self, resolution: str, tile_keys: List[str]) -> Optional[str]:
        """
        Build or refresh a GDAL VRT mosaic from cached tiles.
        
        Args:
            resolution: DEM resolution
            tile_keys: List of tile keys to include in mosaic
        
        Returns:
            Path to VRT file or None if failed
        """
        try:
            import rasterio
            from rasterio.vrt import WarpedVRT
            
            # Collect all existing tile files
            tile_files = []
            for tile_key in tile_keys:
                tile_file = self.target_dir / resolution / tile_key / f"{tile_key}.tif"
                if tile_file.exists():
                    tile_files.append(str(tile_file))
            
            if not tile_files:
                return None
            
            # VRT output path
            vrt_path = self.target_dir / resolution / "mosaic.vrt"
            
            # Build VRT using gdalbuildvrt command
            import subprocess
            cmd = [
                "gdalbuildvrt",
                str(vrt_path),
                *tile_files
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return str(vrt_path)
            else:
                # Fallback: create a simple text-based VRT list
                vrt_list_path = self.target_dir / resolution / "tiles_list.txt"
                with open(vrt_list_path, 'w') as f:
                    for tile_file in tile_files:
                        f.write(f"{tile_file}\n")
                return str(vrt_list_path)
                
        except Exception as e:
            print(f"Warning: Could not build VRT mosaic: {e}")
            return None
    
    async def log_summary(
        self,
        input_params: Dict,
        download_summary: Dict,
        mosaic_path: Optional[str],
        execution_time: float
    ):
        """
        Log operation summary to JSON file.
        
        Args:
            input_params: Input parameters from request
            download_summary: Summary of download operation
            mosaic_path: Path to generated mosaic
            execution_time: Execution time in seconds
        """
        timestamp = datetime.utcnow().isoformat()
        log_filename = f"buildcache_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        log_path = self.log_dir / log_filename
        
        log_data = {
            "timestamp": timestamp,
            "execution_time_seconds": round(execution_time, 2),
            "input_parameters": input_params,
            "download_summary": {
                "total_tiles": download_summary["total_tiles"],
                "downloaded": len(download_summary["downloaded"]),
                "skipped": len(download_summary["skipped"]),
                "failed": len(download_summary["failed"]),
                "total_bytes": download_summary["total_bytes"],
                "downloaded_tiles": download_summary["downloaded"],
                "skipped_tiles": download_summary["skipped"],
                "failed_tiles": download_summary["failed"]
            },
            "mosaic_path": mosaic_path,
            "target_directory": str(self.target_dir)
        }
        
        async with aiofiles.open(log_path, 'w') as f:
            await f.write(json.dumps(log_data, indent=2))
        
        return str(log_path)

