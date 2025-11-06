"""
Service for splitting large geographic areas into 100km squares
"""
import math
from typing import List, Tuple
from geopy.distance import geodesic
from app.models.cachemap import GridSquare


class GridSplitter:
    """
    Splits a large geographic area into approximately 100km × 100km squares.
    """
    
    def __init__(self, square_size_km: float = 100.0):
        """
        Initialize the grid splitter.
        
        Args:
            square_size_km: Target size of each square in kilometers (default: 100km)
        """
        self.square_size_km = square_size_km
    
    def split_into_grid(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float
    ) -> List[GridSquare]:
        """
        Split a bounding box into approximately 100km squares.
        
        The algorithm:
        1. Calculate how many latitude degrees correspond to ~100km
        2. Calculate how many longitude degrees correspond to ~100km at the center latitude
        3. Create a grid of squares with these dimensions
        
        Args:
            min_lat: Southern latitude
            max_lat: Northern latitude
            min_lon: Western longitude
            max_lon: Eastern longitude
        
        Returns:
            List of GridSquare objects
        """
        squares = []
        
        # Calculate center latitude for longitude calculations
        center_lat = (min_lat + max_lat) / 2
        
        # Calculate degrees per 100km for latitude (consistent worldwide)
        # At equator: 1 degree ≈ 111 km, so 100km ≈ 0.9009 degrees
        lat_degrees_per_100km = self.square_size_km / 111.0
        
        # Calculate degrees per 100km for longitude (varies by latitude)
        # At equator: 1 degree ≈ 111 km
        # At latitude L: 1 degree ≈ 111 * cos(L) km
        lon_degrees_per_100km = self.square_size_km / (111.0 * math.cos(math.radians(center_lat)))
        
        # Generate grid squares
        current_lat = min_lat
        lat_index = 0
        
        while current_lat < max_lat:
            next_lat = min(current_lat + lat_degrees_per_100km, max_lat)
            
            current_lon = min_lon
            lon_index = 0
            
            while current_lon < max_lon:
                next_lon = min(current_lon + lon_degrees_per_100km, max_lon)
                
                # Calculate center point
                square_center_lat = (current_lat + next_lat) / 2
                square_center_lon = (current_lon + next_lon) / 2
                
                # Create square ID
                square_id = f"square_{lat_index}_{lon_index}"
                
                # Create GridSquare object
                square = GridSquare(
                    square_id=square_id,
                    min_lat=current_lat,
                    max_lat=next_lat,
                    min_lon=current_lon,
                    max_lon=next_lon,
                    center_lat=square_center_lat,
                    center_lon=square_center_lon
                )
                
                squares.append(square)
                
                current_lon = next_lon
                lon_index += 1
            
            current_lat = next_lat
            lat_index += 1
        
        return squares
    
    def calculate_square_dimensions(self, square: GridSquare) -> Tuple[float, float]:
        """
        Calculate the actual dimensions of a square in kilometers.
        
        Args:
            square: GridSquare object
        
        Returns:
            Tuple of (north_south_km, east_west_km)
        """
        # North-south distance (latitude)
        north_south_km = geodesic(
            (square.min_lat, square.center_lon),
            (square.max_lat, square.center_lon)
        ).kilometers
        
        # East-west distance (longitude)
        east_west_km = geodesic(
            (square.center_lat, square.min_lon),
            (square.center_lat, square.max_lon)
        ).kilometers
        
        return north_south_km, east_west_km
    
    def calculate_total_area(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float
    ) -> Tuple[float, float]:
        """
        Calculate the total dimensions of the area.
        
        Args:
            min_lat: Southern latitude
            max_lat: Northern latitude
            min_lon: Western longitude
            max_lon: Eastern longitude
        
        Returns:
            Tuple of (north_south_km, east_west_km)
        """
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # North-south distance
        north_south_km = geodesic(
            (min_lat, center_lon),
            (max_lat, center_lon)
        ).kilometers
        
        # East-west distance
        east_west_km = geodesic(
            (center_lat, min_lon),
            (center_lat, max_lon)
        ).kilometers
        
        return north_south_km, east_west_km

