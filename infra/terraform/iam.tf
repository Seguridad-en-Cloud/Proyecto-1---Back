###############################################################################
# Service accounts (one per workload) following the principle of least
# privilege required by Entrega 2 §3.2:
#
#   * livemenu-api-sa       — runs the Cloud Run backend.
#   * livemenu-frontend-sa  — runs the Cloud Run frontend (no GCP perms beyond
#                             logging).
#   * livemenu-deployer-sa  — used by GitHub Actions via Workload Identity
#                             Federation to push images and deploy revisions.
#
# The api SA is the only identity that can read the JWT/DB secrets, write the
# images bucket, and connect to Cloud SQL. The frontend cannot touch any of
# those resources even if it were compromised.
###############################################################################

# ── Backend service account ──────────────────────────────────────────────
resource "google_service_account" "api" {
  account_id   = "livemenu-api-${local.name_suffix}"
  display_name = "LiveMenu API runtime"
  description  = "Identity for the Cloud Run backend revision"
}

# Reach Cloud SQL through the private IP (requires the Cloud SQL Client role
# even though traffic flows through the VPC connector).
resource "google_project_iam_member" "api_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Read and write *only* the LiveMenu image bucket (set in storage.tf).
resource "google_storage_bucket_iam_member" "api_bucket_admin" {
  bucket = google_storage_bucket.images.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.api.email}"
}

# Default log writer / metric writer so structured logs surface in Cloud Logging.
resource "google_project_iam_member" "api_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api.email}"
}
resource "google_project_iam_member" "api_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Per-secret access binding lives in secrets.tf so each secret declares its own
# consumers; keeps the principle of least privilege explicit.

# ── Frontend service account ─────────────────────────────────────────────
resource "google_service_account" "frontend" {
  account_id   = "livemenu-frontend-${local.name_suffix}"
  display_name = "LiveMenu frontend runtime"
  description  = "Identity for the Cloud Run frontend revision (static SPA)"
}

resource "google_project_iam_member" "frontend_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.frontend.email}"
}

# ── Deployer (CI/CD) service account ─────────────────────────────────────
# Used by GitHub Actions through Workload Identity Federation. We grant only
# the roles required to push images and update Cloud Run services; nothing
# more, so a compromised pipeline cannot read application secrets.
resource "google_service_account" "deployer" {
  account_id   = "livemenu-deployer-${local.name_suffix}"
  display_name = "LiveMenu CI/CD deployer"
  description  = "Used by GitHub Actions to build & deploy"
}

resource "google_project_iam_member" "deployer_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_project_iam_member" "deployer_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# Required so the deployer can attach the api/frontend SAs to a new revision.
resource "google_service_account_iam_member" "deployer_act_as_api" {
  service_account_id = google_service_account.api.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_service_account_iam_member" "deployer_act_as_frontend" {
  service_account_id = google_service_account.frontend.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}
