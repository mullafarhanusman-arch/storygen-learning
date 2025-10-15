variable "gcp_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "gcp_region" {
  description = "The GCP region."
  type        = string
}

variable "gcp_artifact_registry_repository" {
  description = "The Artifact Registry repository name."
  type        = string
}

variable "frontend_image_name" {
  description = "The name of the frontend Docker image."
  type        = string
}

variable "backend_image_name" {
  description = "The name of the backend Docker image."
  type        = string
}

variable "service_account_name" {
  description = "The name of the service account."
  type        = string
}

variable "story_bucket_name" {
  description = "The name of the GCS bucket for stories."
  type        = string
  default     = "storygen-stories-bucket"
}

variable "image_bucket_name" {
  description = "The name of the GCS bucket for images."
  type        = string
  default     = "storygen-images-bucket"
}
