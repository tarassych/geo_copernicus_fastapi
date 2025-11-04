#!/bin/bash

# Deployment script for GCP Cloud Run
# Usage: ./deploy.sh [project-id] [region]

set -e

# Configuration
PROJECT_ID=${1:-"your-gcp-project-id"}
REGION=${2:-"us-central1"}
SERVICE_NAME="copernicus-fastapi"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Copernicus FastAPI to GCP Cloud Run"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
echo "📝 Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# Build the container
echo "🏗️  Building Docker container..."
gcloud builds submit --tag ${IMAGE_NAME}

# Create secret for environment variables (if it doesn't exist)
echo "🔐 Setting up secrets..."
if ! gcloud secrets describe AppSecretsFromDotEnv &> /dev/null; then
    echo "Creating AppSecretsFromDotEnv secret with .env format..."
    echo "Please enter your OpenTopography API key:"
    read -s API_KEY
    
    # Create .env format secret
    cat << EOF | gcloud secrets create AppSecretsFromDotEnv --data-file=-
TARGET_DIR=tilescache
LOG_DIR=logs
TOPO_API_KEY=${API_KEY}
EOF
    
    echo "✅ Secret created in .env format"
else
    echo "✅ Secret AppSecretsFromDotEnv already exists"
    echo "To update it, run:"
    echo "  cat .env | gcloud secrets versions add AppSecretsFromDotEnv --data-file=-"
fi

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --update-secrets AppSecretsFromDotEnv=AppSecretsFromDotEnv:latest

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Deployment successful!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "🧪 Test your endpoints:"
echo "  Health Check:  ${SERVICE_URL}/healthcheck"
echo "  API Docs:      ${SERVICE_URL}/docs"
echo ""
echo "📝 Example API calls:"
echo "  curl ${SERVICE_URL}/healthcheck"
echo "  curl '${SERVICE_URL}/elevation/point?latitude=50.7096667&longitude=26.2353500'"
echo ""

