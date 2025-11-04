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

# Create secret for API key (if it doesn't exist)
echo "🔐 Setting up secrets..."
if ! gcloud secrets describe TOPO_API_KEY &> /dev/null; then
    echo "Creating TOPO_API_KEY secret..."
    echo "Please enter your OpenTopography API key:"
    read -s API_KEY
    echo -n "${API_KEY}" | gcloud secrets create TOPO_API_KEY --data-file=-
    echo "✅ Secret created"
else
    echo "✅ Secret TOPO_API_KEY already exists"
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
    --set-env-vars TARGET_DIR=tilescache,LOG_DIR=logs \
    --set-secrets TOPO_API_KEY=TOPO_API_KEY:latest

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

