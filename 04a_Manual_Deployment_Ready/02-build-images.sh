#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Load environment variables
source load-env.sh

# --- Main Script ---

# 1. Configure Docker to use gcloud as a credential helper
echo "Configuring Docker to use gcloud as a credential helper..."
gcloud auth configure-docker "$GCP_REGION-docker.pkg.dev"

# 2. Build and push the backend image using Google Cloud Build
echo "
Building and pushing the backend image..."
gcloud builds submit ./backend --tag "$GCP_REGION-docker.pkg.dev/$GCP_PROJECT_ID/$GCP_ARTIFACT_REGISTRY_REPOSITORY/$BACKEND_IMAGE_NAME:latest"

# 3. Build and push the frontend image using Google Cloud Build
echo "
Building and pushing the frontend image..."
gcloud builds submit ./frontend --tag "$GCP_REGION-docker.pkg.dev/$GCP_PROJECT_ID/$GCP_ARTIFACT_REGISTRY_REPOSITORY/$FRONTEND_IMAGE_NAME:latest"

echo "
Docker images built and pushed successfully!"
