# Copernicus FastAPI

A FastAPI application for Copernicus data services.

## Project Structure

```
.
├── main.py                     # Application entry point
├── app/
│   ├── __init__.py            # App factory
│   ├── config.py              # Configuration management
│   ├── models/                # Pydantic models for validation
│   │   ├── __init__.py
│   │   ├── buildcache.py      # BuildCache models
│   │   └── elevation.py       # Elevation models
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   ├── tile_utils.py      # Tile calculation utilities
│   │   ├── opentopography.py  # OpenTopography API service
│   │   └── elevation_service.py # Elevation query service
│   └── routers/               # API endpoints organized by URL
│       ├── __init__.py
│       ├── healthcheck.py     # /healthcheck endpoint
│       ├── buildcache.py      # /buildcache endpoint
│       └── elevation.py       # /elevation endpoints
├── tilescache/                # Cached DEM tiles (created on first run)
├── logs/                      # Operation logs (created on first run)
├── .env                       # Environment variables (not committed)
├── .env.example               # Example environment variables
├── requirements.txt
└── README.md
```

## Configuration

The application uses environment variables for configuration. Copy the example file and customize as needed:

```bash
cp .env.example .env
```

### Environment Variables

- `TARGET_DIR`: Directory path for tiles cache (default: `tilescache`)
- `LOG_DIR`: Directory path for operation logs (default: `logs`)
- `TOPO_API_KEY`: Your OpenTopography API key (required) - Get one at [https://portal.opentopography.org/requestService](https://portal.opentopography.org/requestService)

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Development mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production mode
```bash
python main.py
```

## API Endpoints

### Health Check
- **GET** `/healthcheck`
  - Returns API status and configuration
  - Response: `{"status": "OK", "target_dir": "tilescache"}`

### Elevation Query
- **GET** `/elevation/point`
  - Get elevation for a specific coordinate point
  - **Required Parameters:**
    - `latitude` (float): Latitude in decimal degrees (-90 to 90)
    - `longitude` (float): Longitude in decimal degrees (-180 to 180)
  - **Optional Parameters:**
    - `resolution` (string): DEM resolution - "GLO-30" (30m, default) or "GLO-90" (90m)
  - **Example Request:**
    ```bash
    curl "http://localhost:8000/elevation/point?latitude=50.7096667&longitude=26.2353500&resolution=GLO-30"
    ```
  - **Example Response:**
    ```json
    {
      "latitude": 50.7096667,
      "longitude": 26.23535,
      "elevation_meters": 172.94,
      "resolution": "GLO-30",
      "tile_used": "N50E026",
      "data_source": "Copernicus DEM",
      "status": "success",
      "message": null
    }
    ```
  - **Note:** The tile containing the point must be cached first using `/buildcache`

- **GET** `/elevation/check`
  - Check if a tile is available for given coordinates
  - Same parameters as `/elevation/point`
  - Returns availability status and tile information

- **GET** `/elevation/difference`
  - Calculate elevation difference between two points
  - **Required Parameters:**
    - `point1_latitude` (float): Latitude of first point (-90 to 90)
    - `point1_longitude` (float): Longitude of first point (-180 to 180)
    - `point2_latitude` (float): Latitude of second point (-90 to 90)
    - `point2_longitude` (float): Longitude of second point (-180 to 180)
  - **Optional Parameters:**
    - `resolution` (string): DEM resolution - "GLO-30" (30m, default) or "GLO-90" (90m)
  - **Example Request:**
    ```bash
    curl "http://localhost:8000/elevation/difference?point1_latitude=50.763240&point1_longitude=26.147292&point2_latitude=50.597127&point2_longitude=26.315736"
    ```
  - **Example Response:**
    ```json
    {
      "point1": {
        "latitude": 50.76324,
        "longitude": 26.147292,
        "elevation_meters": 182.34,
        "tile_used": "N50E026"
      },
      "point2": {
        "latitude": 50.597127,
        "longitude": 26.315736,
        "elevation_meters": 241.99,
        "tile_used": "N50E026"
      },
      "elevation_difference_meters": 59.65,
      "horizontal_distance_meters": 21981.92,
      "slope_degrees": 0.16,
      "slope_percentage": 0.27,
      "resolution": "GLO-30",
      "data_source": "Copernicus DEM",
      "status": "success",
      "message": null
    }
    ```
  - **Returns:**
    - Elevation for both points
    - Elevation difference (point2 - point1)
      - Positive: point2 is higher
      - Negative: point2 is lower
    - Horizontal distance (geodesic distance in meters)
    - Slope angle (degrees)
    - Slope percentage (rise/run × 100)
  - **Use Cases:**
    - Hiking trail difficulty assessment
    - Road grade calculation
    - Terrain analysis
    - Viewshed studies

### Build Cache
- **GET** `/buildcache`
  - Downloads and caches Copernicus DEM tiles from OpenTopography
  - **What it does:**
    1. Validates and normalizes AOI (Area of Interest)
    2. Applies optional buffer and clamps to valid lat/lon
    3. Computes required 1×1° tiles
    4. Downloads tiles from OpenTopography API
    5. Checks cache before downloading (unless force_update=true)
    6. Builds/refreshes GDAL VRT mosaic
    7. Logs operation summary to JSON file
  
  - **Required Parameters:**
    - `min_lat` (float): Southern latitude of bounding box (-90 to 90)
    - `max_lat` (float): Northern latitude of bounding box (-90 to 90, must be > min_lat)
    - `min_lon` (float): Western longitude of bounding box (-180 to 180)
    - `max_lon` (float): Eastern longitude of bounding box (-180 to 180, must be > min_lon)
  
  - **Optional Parameters:**
    - `resolution` (string): DEM resolution - "GLO-30" (30m, default) or "GLO-90" (90m)
    - `buffer_km` (float): Extra margin around bounding box in kilometers
    - `force_update` (boolean): Redownload files even if they exist (default: false)
  
  - **Validation Rules:**
    - max_lat must be greater than min_lat
    - max_lon must be greater than min_lon
    - Bounding box cannot exceed 100 km on any side (north-south or east-west)
  
  - **Example Request:**
    ```bash
    curl "http://localhost:8000/buildcache?min_lat=48.5&max_lat=49.4&min_lon=23.3&max_lon=24.1&resolution=GLO-30&buffer_km=10"
    ```
  
  - **Example Response:**
    ```json
    {
      "status": "success",
      "message": "Cache build completed. Downloaded 2 tiles, skipped 0 existing tiles, 0 failed.",
      "parameters": {
        "original_bounding_box": {...},
        "normalized_bounding_box": {...},
        "resolution": "GLO-30",
        "buffer_km": 10,
        "force_update": false,
        "target_dir": "tilescache"
      },
      "distances": {
        "north_south_km": 100.09,
        "east_west_km": 58.23,
        "max_allowed_km": 100.0
      },
      "tiles": {
        "required_tiles": ["N48E023", "N49E023"],
        "tile_count": 2
      },
      "download_summary": {
        "downloaded": ["N48E023", "N49E023"],
        "skipped": [],
        "failed": [],
        "total_bytes": 54321789,
        "total_tiles": 2
      },
      "mosaic_path": "tilescache/GLO-30/mosaic.vrt",
      "log_file": "logs/buildcache_20251104_123456.json",
      "execution_time_seconds": 12.34
    }
    ```

## Interactive API Documentation

Once the server is running, you can access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing the Health Check

```bash
curl http://localhost:8000/healthcheck
```

Expected response:
```json
{"status": "OK", "target_dir": "tilescache"}
```

## OpenTopography API

This application uses the OpenTopography API to download Copernicus DEM data. 

### Getting an API Key

1. Visit [OpenTopography Portal](https://portal.opentopography.org/requestService)
2. Create an account or log in
3. Request an API key
4. Add the API key to your `.env` file:
   ```
   TOPO_API_KEY=your_actual_api_key_here
   ```

### Tile Storage Structure

Downloaded tiles are organized in the following structure:
```
tilescache/
├── GLO-30/                    # 30m resolution tiles
│   ├── N48E023/
│   │   └── N48E023.tif
│   ├── N49E023/
│   │   └── N49E023.tif
│   └── mosaic.vrt             # GDAL VRT mosaic (if GDAL installed)
└── GLO-90/                    # 90m resolution tiles
    └── ...
```

### Operation Logs

Each cache build operation creates a detailed JSON log:
```
logs/
└── buildcache_20251104_123456.json
```

Log contents include:
- Timestamp and execution time
- Input parameters (original and normalized bounding boxes)
- Download summary (tiles downloaded, skipped, failed)
- Total bytes downloaded
- Paths to mosaic and cached data

## Working with Copernicus DEM

This API is designed for working with Copernicus Digital Elevation Model (DEM) data:

- **GLO-30**: 30-meter resolution (Copernicus DEM)
- **GLO-90**: 90-meter resolution (Copernicus DEM)

The data covers the entire globe and can be used for:
- Elevation queries by coordinates
- Terrain analysis
- Viewshed calculations
- Slope and aspect computations
- 3D visualization

## Usage Workflow

### 1. Download DEM tiles for your area
First, cache the tiles you need:
```bash
curl "http://localhost:8000/buildcache?min_lat=50.5&max_lat=51.0&min_lon=26.0&max_lon=26.5&resolution=GLO-30"
```

### 2. Query elevation for specific points
Once tiles are cached, query elevations:
```bash
curl "http://localhost:8000/elevation/point?latitude=50.7096667&longitude=26.2353500"
```

### 3. Check tile availability (optional)
Before querying, check if a tile is cached:
```bash
curl "http://localhost:8000/elevation/check?latitude=50.7096667&longitude=26.2353500"
```

### 4. Calculate elevation difference between points
Compare elevations and calculate slope:
```bash
curl "http://localhost:8000/elevation/difference?point1_latitude=50.76&point1_longitude=26.15&point2_latitude=50.60&point2_longitude=26.32"
```

## Features

✅ **RESTful API** - Clean, well-documented endpoints  
✅ **Automatic tile management** - Downloads only missing tiles  
✅ **Cache efficiency** - Skips existing files, instant re-queries  
✅ **Coordinate validation** - Comprehensive input validation  
✅ **Distance limits** - Prevents oversized requests (100km max)  
✅ **Multiple resolutions** - Support for 30m and 90m DEMs  
✅ **Detailed logging** - JSON logs for all operations  
✅ **Error handling** - Clear error messages and status codes  
✅ **Fast elevation queries** - Direct GeoTIFF reading with rasterio  
✅ **Async operations** - Parallel tile downloads for performance

