output "lb_ip_address" {
  description = "Static IP of the global HTTPS load balancer. Point your DNS A record here."
  value       = google_compute_global_address.lb_ip.address
}

output "domain_name" {
  description = "Domain expected by the managed SSL certificate (empty if testing without a domain)."
  value       = var.domain_name
}

output "api_service_url" {
  description = "Cloud Run URL for the API. Useful for direct smoke tests; production traffic should go through the LB."
  value       = google_cloud_run_v2_service.api.uri
}

output "frontend_service_url" {
  description = "Cloud Run URL for the frontend SPA."
  value       = google_cloud_run_v2_service.frontend.uri
}

output "cloud_sql_connection_name" {
  description = "Connection name passed to Cloud Run as CLOUD_SQL_CONNECTION_NAME."
  value       = google_sql_database_instance.postgres.connection_name
}

output "cloud_sql_private_ip" {
  description = "Private IP of the Cloud SQL instance (only reachable through the VPC connector)."
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "images_bucket" {
  description = "GCS bucket holding the processed image variants."
  value       = google_storage_bucket.images.name
}

output "artifact_registry_repository" {
  description = "Docker repository path for tagging images."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.containers.repository_id}"
}

output "deployer_service_account" {
  description = "Service account used by GitHub Actions to deploy. Configure WIF impersonation against this email."
  value       = google_service_account.deployer.email
}

output "secret_ids" {
  description = "Names of the secrets stored in Secret Manager."
  value       = [for s in google_secret_manager_secret.rotating : s.secret_id]
}
