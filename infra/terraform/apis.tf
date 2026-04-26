###############################################################################
# Enable the GCP services we depend on. ``disable_on_destroy = false`` means
# ``terraform destroy`` does NOT disable the API project-wide — important when
# the same project is shared by other students.
###############################################################################

locals {
  required_apis = [
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
    "cloudkms.googleapis.com",
  ]
}

resource "google_project_service" "enabled" {
  for_each = toset(local.required_apis)

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
