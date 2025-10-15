#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Load environment variables
source load-env.sh

# --- Main Script ---

# 1. Navigate to the terraform directory
cd terraform_code

# 2. Initialize Terraform
echo "Initializing Terraform..."
terraform init -backend-config="bucket=$TERRAFORM_STATE_BUCKET_NAME"

# 3. Apply Terraform configuration
echo "
Applying Terraform configuration..."
terraform apply -auto-approve \
  -var="gcp_project_id=$GCP_PROJECT_ID" \
  -var="gcp_region=$GCP_REGION" \
  -var="gcp_artifact_registry_repository=$GCP_ARTIFACT_REGISTRY_REPOSITORY" \
  -var="frontend_image_name=$FRONTEND_IMAGE_NAME" \
  -var="backend_image_name=$BACKEND_IMAGE_NAME" \
  -var="service_account_name=$GCP_SERVICE_ACCOUNT_NAME"

# 4. Navigate back to the root directory
cd ..

echo "
Infrastructure deployed successfully!"

