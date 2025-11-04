# Deployment Guide - GCP Cloud Run

This guide covers deploying the Copernicus FastAPI application to Google Cloud Platform (GCP) Cloud Run.

## Prerequisites

1. **GCP Account**: Active Google Cloud Platform account
2. **gcloud CLI**: Install from [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install)
3. **Docker**: For local testing (optional)
4. **OpenTopography API Key**: Get from [opentopography.org](https://opentopography.org/)

## Quick Deployment

### Option 1: Automated Deployment Script

```bash
# Make script executable (already done)
chmod +x deploy.sh

# Deploy to GCP (replace with your project ID)
./deploy.sh your-gcp-project-id us-central1
```

The script will:
- ✅ Enable required GCP APIs
- ✅ Build the Docker container
- ✅ Create secrets for API keys
- ✅ Deploy to Cloud Run
- ✅ Configure resources and environment

### Option 2: Manual Deployment

#### Step 1: Set up GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

# Configure gcloud
gcloud config set project ${PROJECT_ID}

# Enable required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com
```

#### Step 2: Create Secret for API Key

```bash
# Create secret for OpenTopography API key
echo -n "your_opentopography_api_key" | \
    gcloud secrets create TOPO_API_KEY --data-file=-

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding TOPO_API_KEY \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### Step 3: Build Container

```bash
# Build using Cloud Build
gcloud builds submit --tag gcr.io/${PROJECT_ID}/copernicus-fastapi

# OR build locally and push
docker build -t gcr.io/${PROJECT_ID}/copernicus-fastapi .
docker push gcr.io/${PROJECT_ID}/copernicus-fastapi
```

#### Step 4: Deploy to Cloud Run

```bash
gcloud run deploy copernicus-fastapi \
    --image gcr.io/${PROJECT_ID}/copernicus-fastapi \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars TARGET_DIR=tilescache,LOG_DIR=logs \
    --set-secrets TOPO_API_KEY=TOPO_API_KEY:latest
```

### Option 3: Continuous Deployment with Cloud Build

The included `cloudbuild.yaml` enables automatic deployments:

```bash
# Connect your GitHub repository to Cloud Build
gcloud beta builds triggers create github \
    --repo-name=geo_copernicus_fastapi \
    --repo-owner=tarassych \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml

# Now every push to main branch will trigger automatic deployment
```

## Configuration

### Environment Variables

Set in Cloud Run deployment:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Cloud Run auto-sets this |
| `TARGET_DIR` | `tilescache` | DEM tiles cache directory |
| `LOG_DIR` | `logs` | Operation logs directory |
| `TOPO_API_KEY` | - | From Secret Manager |

### Resource Configuration

Recommended settings for production:

```yaml
Memory: 2Gi          # Handles large GeoTIFF files
CPU: 2               # Parallel tile processing
Timeout: 300s        # 5 minutes for large downloads
Max Instances: 10    # Auto-scaling limit
Min Instances: 0     # Scale to zero when idle
```

### Cost Optimization

```bash
# For development (lower costs):
gcloud run deploy copernicus-fastapi \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 2 \
    --min-instances 0

# For production (better performance):
gcloud run deploy copernicus-fastapi \
    --memory 4Gi \
    --cpu 4 \
    --max-instances 100 \
    --min-instances 1
```

## Local Testing with Docker

### Build and Run Locally

```bash
# Build the image
docker build -t copernicus-fastapi .

# Run locally
docker run -p 8080:8080 \
    -e TOPO_API_KEY="your_api_key" \
    copernicus-fastapi

# Test the endpoints
curl http://localhost:8080/healthcheck
curl http://localhost:8080/docs
```

### Test with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - TOPO_API_KEY=${TOPO_API_KEY}
      - TARGET_DIR=tilescache
      - LOG_DIR=logs
    volumes:
      - ./tilescache:/app/tilescache
      - ./logs:/app/logs
```

Run with:
```bash
docker-compose up
```

## Monitoring and Logs

### View Logs

```bash
# Real-time logs
gcloud run services logs tail copernicus-fastapi --region=${REGION}

# Recent logs
gcloud run services logs read copernicus-fastapi --region=${REGION} --limit=100
```

### Cloud Console

Access logs in Cloud Console:
- Navigate to: Cloud Run → copernicus-fastapi → Logs
- Filter by severity, timeframe, or text search

### Metrics

Monitor in Cloud Console:
- **Request count**: Number of API calls
- **Request latency**: Response times
- **Container CPU/Memory**: Resource usage
- **Error rate**: Failed requests

## Troubleshooting

### Common Issues

#### 1. API Key Not Working
```bash
# Update secret
echo -n "new_api_key" | gcloud secrets versions add TOPO_API_KEY --data-file=-

# Redeploy to pick up new secret
gcloud run services update copernicus-fastapi --region=${REGION}
```

#### 2. Out of Memory Errors
```bash
# Increase memory allocation
gcloud run services update copernicus-fastapi \
    --memory 4Gi \
    --region=${REGION}
```

#### 3. Timeout Errors
```bash
# Increase timeout
gcloud run services update copernicus-fastapi \
    --timeout 600 \
    --region=${REGION}
```

#### 4. Permission Denied for Secrets
```bash
# Grant access to service account
gcloud secrets add-iam-policy-binding TOPO_API_KEY \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Security Best Practices

1. **Authentication**: For production, consider removing `--allow-unauthenticated`
2. **Secrets**: Never commit API keys, use Secret Manager
3. **IAM**: Grant minimum required permissions
4. **VPC**: Consider VPC connector for private resources
5. **Rate Limiting**: Implement API rate limits

## Cost Estimation

Cloud Run pricing (approximate):

- **CPU**: $0.00002400/vCPU-second
- **Memory**: $0.00000250/GiB-second
- **Requests**: $0.40/million requests

Example monthly costs:
- **Low traffic**: $5-20/month (few requests/day)
- **Medium traffic**: $50-200/month (1000s requests/day)
- **High traffic**: $500+/month (millions requests/month)

Free tier includes:
- 2 million requests/month
- 360,000 GiB-seconds of memory
- 180,000 vCPU-seconds

## Updates and Rollbacks

### Deploy New Version

```bash
# Build new version
gcloud builds submit --tag gcr.io/${PROJECT_ID}/copernicus-fastapi:v2

# Deploy with tag
gcloud run deploy copernicus-fastapi \
    --image gcr.io/${PROJECT_ID}/copernicus-fastapi:v2 \
    --region ${REGION}
```

### Rollback to Previous Version

```bash
# List revisions
gcloud run revisions list --service=copernicus-fastapi --region=${REGION}

# Rollback to specific revision
gcloud run services update-traffic copernicus-fastapi \
    --to-revisions=copernicus-fastapi-00001-abc=100 \
    --region=${REGION}
```

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## Support

For issues specific to this deployment:
- Check logs: `gcloud run services logs read`
- Review metrics in Cloud Console
- Verify secrets configuration
- Test locally with Docker first

For GCP Cloud Run issues:
- [Cloud Run Troubleshooting](https://cloud.google.com/run/docs/troubleshooting)
- [Stack Overflow - google-cloud-run](https://stackoverflow.com/questions/tagged/google-cloud-run)

