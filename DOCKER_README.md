# Docker Deployment Guide

## Quick Start

### Build the Docker Image

```bash
docker build -t copernicus-fastapi .
```

### Run Locally

```bash
# Run with environment variable
docker run -p 8080:8080 \
  -e TOPO_API_KEY="your_api_key_here" \
  copernicus-fastapi

# Run with .env file
docker run -p 8080:8080 \
  --env-file .env \
  copernicus-fastapi

# Run with persistent volumes
docker run -p 8080:8080 \
  -e TOPO_API_KEY="your_api_key" \
  -v $(pwd)/tilescache:/app/tilescache \
  -v $(pwd)/logs:/app/logs \
  copernicus-fastapi
```

### Test the API

```bash
# Health check
curl http://localhost:8080/healthcheck

# API documentation
open http://localhost:8080/docs
```

## Dockerfile Features

### ✅ Production Ready
- **Multi-stage optimization**: Slim Python 3.11 base image
- **Security**: Non-root user (appuser)
- **Health checks**: Built-in health check endpoint
- **Cloud Run compatible**: Respects PORT environment variable

### 🔧 Technical Stack
- **Base Image**: `python:3.11-slim`
- **GDAL/Rasterio**: Full geospatial support
- **System Dependencies**: Minimal for smaller image size
- **Default Port**: 8080 (configurable via PORT env var)

### 📦 Image Size
- Approximate size: **~800MB** (includes GDAL)
- Without GDAL: **~400MB**

## GCP Cloud Run Deployment

### Prerequisites
1. GCP account with billing enabled
2. gcloud CLI installed and configured
3. OpenTopography API key

### One-Command Deployment

```bash
chmod +x deploy.sh
./deploy.sh your-project-id us-central1
```

### What Gets Deployed
- **Memory**: 2GB (handles large GeoTIFF files)
- **CPU**: 2 vCPUs (parallel processing)
- **Timeout**: 5 minutes (tile downloads)
- **Scaling**: 0-10 instances (auto-scale)
- **Region**: Configurable (default: us-central1)

### Cost Estimate
- **Idle**: $0/month (scales to zero)
- **Light use**: $5-20/month
- **Moderate use**: $50-200/month
- **Free tier**: 2M requests/month included

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `8080` | Server port (Cloud Run sets this) |
| `TARGET_DIR` | No | `tilescache` | DEM cache directory |
| `LOG_DIR` | No | `logs` | Log files directory |
| `TOPO_API_KEY` | Yes | - | OpenTopography API key |

## File Structure in Container

```
/app/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── app/                    # Application code
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   ├── routers/
│   └── services/
├── tilescache/            # DEM tile cache (created at runtime)
└── logs/                  # Operation logs (created at runtime)
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs <container-id>

# Test build locally
docker build --no-cache -t copernicus-fastapi .
```

### Out of memory
```bash
# Run with more memory
docker run -m 4g -p 8080:8080 copernicus-fastapi

# On Cloud Run
gcloud run services update copernicus-fastapi --memory 4Gi
```

### GDAL/Rasterio errors
```bash
# Verify GDAL installation in container
docker run copernicus-fastapi gdalinfo --version

# Check environment variables
docker run copernicus-fastapi env | grep GDAL
```

## Advanced Usage

### Custom Build Args

```bash
# Specify Python version
docker build --build-arg PYTHON_VERSION=3.11 -t copernicus-fastapi .
```

### Multi-Architecture Build

```bash
# Build for ARM and AMD
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t copernicus-fastapi:multi \
  --push .
```

### Development Mode

```bash
# Mount source code for live reload
docker run -p 8080:8080 \
  -v $(pwd):/app \
  -e TOPO_API_KEY="your_key" \
  copernicus-fastapi \
  uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

## Security Notes

1. **Never commit API keys** - Use environment variables or secrets
2. **Use Secret Manager** - On GCP for production
3. **Non-root user** - Container runs as appuser (UID 1000)
4. **Minimal base image** - Reduced attack surface
5. **.dockerignore** - Prevents sensitive file inclusion

## Additional Resources

- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [README.md](README.md) - API documentation
