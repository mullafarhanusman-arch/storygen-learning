provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_project_service_identity" "run_sa" {
  provider = google-beta
  project  = var.gcp_project_id
  service  = "run.googleapis.com"
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = "storygen-frontend"
  location = var.gcp_region

  template {
    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${var.gcp_artifact_registry_repository}/${var.frontend_image_name}:latest"
      ports {
        container_port = 3000
      }
      env {
        name  = "NEXT_PUBLIC_WS_URL"
        value = replace(google_cloud_run_v2_service.backend.uri, "https", "wss")
      }
    }
    service_account = "${var.service_account_name}@${var.gcp_project_id}.iam.gserviceaccount.com"
  }

  traffic {
    percent         = 100
    type            = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
  depends_on = [google_cloud_run_v2_service.backend]
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_v2_service.frontend.location
  project  = google_cloud_run_v2_service.frontend.project
  service  = google_cloud_run_v2_service.frontend.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

resource "google_cloud_run_v2_service" "backend" {
  name     = "storygen-backend"
  location = var.gcp_region

  template {
    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${var.gcp_artifact_registry_repository}/${var.backend_image_name}:latest"
      ports {
        container_port = 8080
      }
      env {
        name = "STORY_BUCKET"
        value = google_storage_bucket.story_bucket.name
      }
      env {
        name = "IMAGE_BUCKET"
        value = google_storage_bucket.image_bucket.name
      }
    }
    service_account = "${var.service_account_name}@${var.gcp_project_id}.iam.gserviceaccount.com"
  }

  traffic {
    percent         = 100
    type            = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

resource "google_storage_bucket" "story_bucket" {
  name          = var.story_bucket_name
  location      = var.gcp_region
  force_destroy = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "story_bucket_iam" {
  bucket = google_storage_bucket.story_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_name}@${var.gcp_project_id}.iam.gserviceaccount.com"
}

resource "google_storage_bucket" "image_bucket" {
  name          = var.image_bucket_name
  location      = var.gcp_region
  force_destroy = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "image_bucket_iam" {
  bucket = google_storage_bucket.image_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_name}@${var.gcp_project_id}.iam.gserviceaccount.com"
}