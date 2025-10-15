#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Load environment variables
source load-env.sh

# --- Helper Functions ---

# Check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# --- Main Script ---

# 1. Check for required tools
echo "Checking for required tools..."
for tool in gcloud docker terraform; do
  if ! command_exists "$tool"; then
    echo "Error: $tool is not installed. Please install it and try again."
    exit 1
  fi
done
echo "All required tools are installed."

# 2. Authenticate with GCP
echo "
Authenticating with GCP..."
gcloud auth login
gcloud auth application-default login

# 3. Set GCP project and region
echo "
Configuring GCP project and region..."
gcloud config set project "$GCP_PROJECT_ID"
gcloud config set compute/region "$GCP_REGION"

# 4. Enable required GCP APIs
echo "
Enabling required GCP APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  storage-component.googleapis.com \
  serviceusage.googleapis.com \
  logging.googleapis.com \
  pubsub.googleapis.com

# 5. Create Artifact Registry repository
echo "
Creating Artifact Registry repository..."
if ! gcloud artifacts repositories describe "$GCP_ARTIFACT_REGISTRY_REPOSITORY" --location="$GCP_REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$GCP_ARTIFACT_REGISTRY_REPOSITORY" \
    --repository-format=docker \
    --location="$GCP_REGION" \
    --description="StoryGen Docker repository"
else
  echo "Artifact Registry repository '$GCP_ARTIFACT_REGISTRY_REPOSITORY' already exists."
fi

# 6. Create service account
echo "
Creating service account..."
if ! gcloud iam service-accounts describe "$GCP_SERVICE_ACCOUNT_NAME@$GCP_PROJECT_ID.iam.gserviceaccount.com" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$GCP_SERVICE_ACCOUNT_NAME" \
    --display-name="StoryGen Service Account"
else
  echo "Service account '$GCP_SERVICE_ACCOUNT_NAME' already exists."
fi

# 7. Grant IAM roles to the service account
echo "
Granting IAM roles to the service account..."
SA_EMAIL="$GCP_SERVICE_ACCOUNT_NAME@$GCP_PROJECT_ID.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.invoker"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.admin"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/iam.serviceAccountUser"

# 8. Create GCS bucket for Terraform state
echo "
Creating GCS bucket for Terraform state..."
if ! gsutil ls -b "gs://$TERRAFORM_STATE_BUCKET_NAME" >/dev/null 2>&1; then
  gsutil mb -p "$GCP_PROJECT_ID" -l "$GCP_REGION" "gs://$TERRAFORM_STATE_BUCKET_NAME"
  gsutil versioning set on "gs://$TERRAFORM_STATE_BUCKET_NAME"
else
  echo "GCS bucket '$TERRAFORM_STATE_BUCKET_NAME' already exists."
fi

echo "
Environment setup complete!"
