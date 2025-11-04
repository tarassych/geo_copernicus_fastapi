# Configuration Guide

This guide explains how environment variables are loaded in different environments.

## Overview

The application uses a **dual configuration loading strategy**:

1. **GCP Cloud Run**: Loads all environment variables from the `AppSecretsFromDotEnv` secret in Google Secret Manager
2. **Local Development**: Loads from `.env` file in the project root

The loading logic automatically detects which environment it's running in and uses the appropriate source.

## Configuration Loading Flow

```
┌─────────────────────────────────────────┐
│   Application Startup (config.py)      │
└──────────────┬──────────────────────────┘
               │
               ▼
       ┌───────────────────┐
       │ Check Environment │
       └─────────┬─────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌────────────────┐    ┌──────────────────┐
│ AppSecretsFrom │    │   .env file      │
│ DotEnv exists? │    │   exists?        │
│     (GCP)      │    │   (Local)        │
└────────┬───────┘    └────────┬─────────┘
         │ YES                 │ YES
         ▼                     ▼
┌────────────────┐    ┌──────────────────┐
│ Parse secret   │    │ Load from file   │
│ as .env format │    │ using dotenv     │
└────────┬───────┘    └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
         ┌──────────────────┐
         │ Load into        │
         │ os.environ       │
         └──────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │ Pydantic Settings│
         │ reads from env   │
         └──────────────────┘
```

## Local Development

### Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your actual values:
```env
TARGET_DIR=tilescache
LOG_DIR=logs
TOPO_API_KEY=your_actual_api_key_here
```

3. Run the application:
```bash
uvicorn main:app --reload
```

### How It Works

When the application starts, `app/config.py`:
- Checks if `AppSecretsFromDotEnv` environment variable exists
- If not found (local development), loads from `.env` file
- Prints: `"Loading environment variables from .env"`

## GCP Cloud Run Deployment

### Setup

Create the secret in Google Secret Manager with .env format:

```bash
# Method 1: From .env file
cat .env | gcloud secrets create AppSecretsFromDotEnv --data-file=-

# Method 2: Direct input
cat << 'EOF' | gcloud secrets create AppSecretsFromDotEnv --data-file=-
TARGET_DIR=tilescache
LOG_DIR=logs
TOPO_API_KEY=your_production_api_key_here
EOF

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding AppSecretsFromDotEnv \
    --member="serviceAccount:YOUR_PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Deploy with Secret

Mount the secret as an environment variable in Cloud Run:

```bash
gcloud run deploy copernicus-fastapi \
    --image gcr.io/YOUR_PROJECT_ID/copernicus-fastapi \
    --region us-central1 \
    --update-secrets AppSecretsFromDotEnv=AppSecretsFromDotEnv:latest
```

### How It Works

When the application starts in Cloud Run:
1. Cloud Run mounts `AppSecretsFromDotEnv` secret as an environment variable
2. The secret content is the entire `.env` file content as a string
3. `app/config.py` detects this variable exists
4. It parses the content using `python-dotenv`
5. Variables are loaded into `os.environ`
6. Prints: `"Loading environment variables from GCP Secret Manager (AppSecretsFromDotEnv)"`

## Updating Configuration

### Local Development

Simply edit your `.env` file and restart the application.

### GCP Cloud Run

Update the secret with a new version:

```bash
# Method 1: From updated .env file
cat .env | gcloud secrets versions add AppSecretsFromDotEnv --data-file=-

# Method 2: Direct input
cat << 'EOF' | gcloud secrets versions add AppSecretsFromDotEnv --data-file=-
TARGET_DIR=tilescache
LOG_DIR=logs
TOPO_API_KEY=new_api_key_here
EOF

# Redeploy to pick up new version (Cloud Run will use :latest automatically)
gcloud run deploy copernicus-fastapi --region us-central1
```

## Configuration Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TARGET_DIR` | No | `tilescache` | Directory for DEM tile cache |
| `LOG_DIR` | No | `logs` | Directory for operation logs |
| `TOPO_API_KEY` | Yes | - | OpenTopography API key |
| `PORT` | No | `8080` | Server port (Cloud Run sets this) |

## Verification

### Check Configuration Loading

Call the `/healthcheck` endpoint to verify configuration:

```bash
# Local
curl http://localhost:8000/healthcheck | jq

# Cloud Run
curl https://your-service.run.app/healthcheck | jq
```

Response shows loaded configuration:

```json
{
  "status": "OK",
  "service": "Copernicus DEM FastAPI",
  "environment": {
    "target_dir": "tilescache",
    "log_dir": "logs",
    "port": "8000"
  },
  "api_key_configured": true,
  "endpoints": { ... }
}
```

### Startup Logs

Check application logs to see which source was used:

**Local Development:**
```
Loading environment variables from .env
INFO:     Started server process [12345]
```

**GCP Cloud Run:**
```
Loading environment variables from GCP Secret Manager (AppSecretsFromDotEnv)
INFO:     Started server process [1]
```

## Troubleshooting

### Local: Variables Not Loading

**Problem**: Changes to `.env` file not reflected

**Solutions**:
1. Restart the application completely
2. Verify `.env` file is in project root
3. Check file format (no spaces around `=`)
4. Ensure no quotes around values

### GCP: Variables Not Loading

**Problem**: Application can't read configuration in Cloud Run

**Solutions**:

1. **Verify secret exists:**
```bash
gcloud secrets describe AppSecretsFromDotEnv
```

2. **Check IAM permissions:**
```bash
gcloud secrets get-iam-policy AppSecretsFromDotEnv
```

3. **Verify secret is mounted:**
```bash
gcloud run services describe copernicus-fastapi \
    --region=us-central1 \
    --format="value(spec.template.spec.containers[0].env)"
```

4. **Check Cloud Run logs:**
```bash
gcloud run services logs read copernicus-fastapi \
    --region=us-central1 \
    --limit=50
```

Look for: `"Loading environment variables from GCP Secret Manager"`

### API Key Not Working

**Problem**: `api_key_configured: false` in healthcheck

**Check**:
1. Verify `TOPO_API_KEY` is set in secret/env file
2. Ensure no extra whitespace or quotes
3. Verify API key is valid at OpenTopography
4. Check the key has the right format

## Security Best Practices

1. **Never commit secrets**:
   - `.env` is in `.gitignore`
   - Only commit `.env.example` with placeholder values

2. **Use Secret Manager in production**:
   - Don't set environment variables directly in Cloud Run console
   - Always use Secret Manager for sensitive data

3. **Rotate keys regularly**:
   - Update `AppSecretsFromDotEnv` secret versions
   - Redeploy to apply changes

4. **Limit access**:
   - Only grant Secret Manager access to necessary service accounts
   - Use principle of least privilege

## Alternative: Individual Secrets

If you prefer to manage secrets individually instead of using the `.env` format:

### Disable AppSecretsFromDotEnv

Simply don't create the `AppSecretsFromDotEnv` secret, and instead:

1. Set environment variables directly in Cloud Run:
```bash
gcloud run deploy copernicus-fastapi \
    --set-env-vars TARGET_DIR=tilescache,LOG_DIR=logs \
    --set-secrets TOPO_API_KEY=TOPO_API_KEY:latest
```

2. The application will fall back to reading from `os.environ` directly

**Note**: The `.env` format approach is recommended for easier management and consistency with local development.

## Summary

✅ **Local**: Reads from `.env` file automatically  
✅ **Cloud Run**: Reads from `AppSecretsFromDotEnv` secret automatically  
✅ **Automatic detection**: No code changes needed between environments  
✅ **Consistent format**: Same `.env` format everywhere  
✅ **Easy updates**: Single secret to manage in GCP  

