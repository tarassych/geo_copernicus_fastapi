"""
Utility functions for tile calculations and AOI normalization
"""
import math
from typing import List, Tuple
from geopy.distance import geodesic


def normalize_aoi(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    buffer_km: float = None
) -> Tuple[float, float, float, float]:
    """
    Normalize Area of Interest and apply buffer if specified.
    
    Args:
        min_lat: Southern latitude
        max_lat: Northern latitude
        min_lon: Western longitude
        max_lon: Eastern longitude
        buffer_km: Buffer to add in kilometers (optional)
    
    Returns:
        Tuple of (normalized_min_lat, normalized_max_lat, normalized_min_lon, normalized_max_lon)
    """
    if buffer_km is not None and buffer_km > 0:
        # Calculate approximate degrees for buffer
        # At equator: 1 degree ≈ 111 km
        # For latitude (vertical), this is fairly consistent
        lat_buffer_deg = buffer_km / 111.0
        
        # For longitude (horizontal), it varies by latitude
        # Use average latitude for calculation
        avg_lat = (min_lat + max_lat) / 2
        lon_buffer_deg = buffer_km / (111.0 * math.cos(math.radians(avg_lat)))
        
        # Apply buffer
        min_lat = min_lat - lat_buffer_deg
        max_lat = max_lat + lat_buffer_deg
        min_lon = min_lon - lon_buffer_deg
        max_lon = max_lon + lon_buffer_deg
    
    # Clamp to valid ranges
    min_lat = max(-90.0, min_lat)
    max_lat = min(90.0, max_lat)
    min_lon = max(-180.0, min_lon)
    max_lon = min(180.0, max_lon)
    
    return min_lat, max_lat, min_lon, max_lon


def compute_tile_keys(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float
) -> List[str]:
    """
    Compute 1×1° tile keys for the given bounding box.
    
    Tile naming convention: N49E024 means latitude 49-50°N, longitude 24-25°E
    - Latitude: N (north) or S (south) + 2-digit number
    - Longitude: E (east) or W (west) + 3-digit number
    
    Args:
        min_lat: Southern latitude
        max_lat: Northern latitude
        min_lon: Western longitude
        max_lon: Eastern longitude
    
    Returns:
        List of tile keys (e.g., ['N49E024', 'N49E025', 'N50E024'])
    """
    tiles = []
    
    # Get integer degree ranges
    lat_start = int(math.floor(min_lat))
    lat_end = int(math.ceil(max_lat))
    lon_start = int(math.floor(min_lon))
    lon_end = int(math.ceil(max_lon))
    
    for lat in range(lat_start, lat_end):
        for lon in range(lon_start, lon_end):
            tile_key = format_tile_key(lat, lon)
            tiles.append(tile_key)
    
    return tiles


def format_tile_key(lat: int, lon: int) -> str:
    """
    Format a tile key from integer lat/lon coordinates.
    
    Examples:
        format_tile_key(49, 24) -> "N49E024"
        format_tile_key(-10, -5) -> "S10W005"
        format_tile_key(5, -120) -> "N05W120"
    
    Args:
        lat: Integer latitude
        lon: Integer longitude
    
    Returns:
        Formatted tile key string
    """
    # Latitude: N or S
    lat_dir = "N" if lat >= 0 else "S"
    lat_abs = abs(lat)
    
    # Longitude: E or W
    lon_dir = "E" if lon >= 0 else "W"
    lon_abs = abs(lon)
    
    # Format: N49E024 (lat is 2 digits, lon is 3 digits)
    tile_key = f"{lat_dir}{lat_abs:02d}{lon_dir}{lon_abs:03d}"
    
    return tile_key


def parse_tile_key(tile_key: str) -> Tuple[int, int]:
    """
    Parse a tile key into lat/lon integers.
    
    Args:
        tile_key: Tile key like "N49E024"
    
    Returns:
        Tuple of (lat, lon) as integers
    """
    # Extract direction and numbers
    lat_dir = tile_key[0]
    lon_dir = tile_key[3] if len(tile_key) == 7 else tile_key[4]
    
    if len(tile_key) == 7:
        lat_num = int(tile_key[1:3])
        lon_num = int(tile_key[4:7])
    else:
        lat_num = int(tile_key[1:4])
        lon_num = int(tile_key[5:8])
    
    lat = lat_num if lat_dir == "N" else -lat_num
    lon = lon_num if lon_dir == "E" else -lon_num
    
    return lat, lon

