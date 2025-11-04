"""
Service for querying elevation from cached DEM tiles
"""
import math
from pathlib import Path
from typing import Optional, Tuple
from app.services.tile_utils import format_tile_key


class ElevationService:
    """
    Service for reading elevation values from cached DEM tiles
    """
    
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir)
    
    def get_elevation(
        self,
        latitude: float,
        longitude: float,
        resolution: str = "GLO-30"
    ) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """
        Get elevation for a specific point from cached tiles.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            resolution: DEM resolution (GLO-30 or GLO-90)
        
        Returns:
            Tuple of (elevation_meters, tile_key, error_message)
        """
        # Determine which tile contains this point
        tile_lat = int(math.floor(latitude))
        tile_lon = int(math.floor(longitude))
        tile_key = format_tile_key(tile_lat, tile_lon)
        
        # Check if tile exists in cache
        tile_path = self.target_dir / resolution / tile_key / f"{tile_key}.tif"
        
        if not tile_path.exists():
            return None, tile_key, f"Tile {tile_key} not found in cache. Please run /buildcache first for this area."
        
        try:
            # Read elevation from the tile
            elevation = self._read_elevation_from_tile(
                tile_path,
                latitude,
                longitude,
                tile_lat,
                tile_lon
            )
            return elevation, tile_key, None
            
        except Exception as e:
            return None, tile_key, f"Error reading elevation: {str(e)}"
    
    def _read_elevation_from_tile(
        self,
        tile_path: Path,
        latitude: float,
        longitude: float,
        tile_lat: int,
        tile_lon: int
    ) -> Optional[float]:
        """
        Read elevation value from a specific tile.
        
        Args:
            tile_path: Path to the GeoTIFF file
            latitude: Query latitude
            longitude: Query longitude
            tile_lat: Integer latitude of the tile
            tile_lon: Integer longitude of the tile
        
        Returns:
            Elevation in meters or None if no data
        """
        try:
            # Try using rasterio first (preferred method)
            import rasterio
            from rasterio.windows import from_bounds
            
            with rasterio.open(tile_path) as src:
                # Get the pixel coordinates for the point
                row, col = src.index(longitude, latitude)
                
                # Read the elevation value at that pixel
                # Handle out of bounds
                if 0 <= row < src.height and 0 <= col < src.width:
                    elevation = src.read(1)[row, col]
                    
                    # Check for NoData values
                    if src.nodata is not None and elevation == src.nodata:
                        return None
                    
                    return float(elevation)
                else:
                    return None
                    
        except ImportError:
            # Fallback to GDAL if rasterio is not available
            try:
                from osgeo import gdal
                gdal.UseExceptions()
                
                ds = gdal.Open(str(tile_path))
                if ds is None:
                    return None
                
                # Get geotransform
                gt = ds.GetGeoTransform()
                
                # Convert geographic coordinates to pixel coordinates
                px = int((longitude - gt[0]) / gt[1])
                py = int((latitude - gt[3]) / gt[5])
                
                # Read the band
                band = ds.GetRasterBand(1)
                
                # Check bounds
                if 0 <= px < ds.RasterXSize and 0 <= py < ds.RasterYSize:
                    elevation = band.ReadAsArray(px, py, 1, 1)[0, 0]
                    
                    # Check for NoData
                    nodata = band.GetNoDataValue()
                    if nodata is not None and elevation == nodata:
                        return None
                    
                    return float(elevation)
                else:
                    return None
                    
                ds = None
                
            except ImportError:
                # Final fallback: use simple calculation based on position
                # This is a very basic approximation and should not be used in production
                # It's here only as a last resort
                return self._fallback_elevation_read(
                    tile_path,
                    latitude,
                    longitude,
                    tile_lat,
                    tile_lon
                )
        except Exception as e:
            raise Exception(f"Failed to read elevation from tile: {str(e)}")
    
    def _fallback_elevation_read(
        self,
        tile_path: Path,
        latitude: float,
        longitude: float,
        tile_lat: int,
        tile_lon: int
    ) -> Optional[float]:
        """
        Fallback method using PIL and struct to read raw TIFF data.
        This is a simplified approach that may not work for all GeoTIFF formats.
        """
        try:
            from PIL import Image
            import struct
            
            # Open the TIFF file
            img = Image.open(tile_path)
            
            # Calculate pixel position
            # Assuming the tile is 1 degree x 1 degree
            # and typical Copernicus DEM tiles are 3600x3600 pixels
            width, height = img.size
            
            # Calculate relative position within the tile (0 to 1)
            lat_offset = latitude - tile_lat
            lon_offset = longitude - tile_lon
            
            # Convert to pixel coordinates
            px = int(lon_offset * width)
            py = int((1 - lat_offset) * height)  # Y is inverted in images
            
            # Ensure we're within bounds
            px = max(0, min(px, width - 1))
            py = max(0, min(py, height - 1))
            
            # Get pixel value
            pixel = img.getpixel((px, py))
            
            # If it's a single value, return it
            if isinstance(pixel, (int, float)):
                return float(pixel) if pixel != 0 else None
            
            # If it's a tuple, take the first value
            if isinstance(pixel, tuple):
                return float(pixel[0]) if pixel[0] != 0 else None
            
            return None
            
        except Exception as e:
            raise Exception(f"Fallback elevation read failed: {str(e)}")
    
    def check_tile_availability(
        self,
        latitude: float,
        longitude: float,
        resolution: str = "GLO-30"
    ) -> bool:
        """
        Check if a tile is available in cache for the given coordinates.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            resolution: DEM resolution
        
        Returns:
            True if tile is cached, False otherwise
        """
        tile_lat = int(math.floor(latitude))
        tile_lon = int(math.floor(longitude))
        tile_key = format_tile_key(tile_lat, tile_lon)
        
        tile_path = self.target_dir / resolution / tile_key / f"{tile_key}.tif"
        return tile_path.exists()

