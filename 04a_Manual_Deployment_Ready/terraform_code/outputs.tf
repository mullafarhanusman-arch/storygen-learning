output "frontend_url" {
  description = "The URL of the frontend service."
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_url" {
  description = "The URL of the backend service."
  value       = google_cloud_run_v2_service.backend.uri
}