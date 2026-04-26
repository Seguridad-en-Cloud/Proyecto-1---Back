###############################################################################
# Cloud Storage bucket for image variants (thumbnail/medium/large).
#
# Entrega 2 §4 requires:
#   * Versioning enabled (resilience against accidental deletes by the worker pool).
#   * Encryption at rest (Google-managed key by default; CMEK is documented).
#   * Lifecycle: keep the latest 5 noncurrent versions, delete older ones to
#     bound storage cost.
###############################################################################

resource "google_storage_bucket" "images" {
  name     = "livemenu-images-${var.project_id}-${local.name_suffix}"
  location = var.region

  uniform_bucket_level_access = true   # disables ACLs entirely → IAM only
  public_access_prevention    = "inherited"
  storage_class               = "STANDARD"
  force_destroy               = false

  versioning {
    enabled = true
  }

  # Bound the cost of versioning: keep 5 noncurrent versions OR 30 days,
  # whichever is shorter for an individual object.
  lifecycle_rule {
    condition {
      num_newer_versions = 5
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      days_since_noncurrent_time = 30
      with_state                 = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  # The bucket is fronted by the LB / CDN, never accessed directly by browsers,
  # so we don't need permissive CORS.
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type", "Cache-Control"]
    max_age_seconds = 3600
  }

  labels = local.labels

  depends_on = [google_project_service.enabled]
}

# Public-read so the menu page can serve images via CDN. We use a single
# binding on ``allUsers`` with ``objectViewer`` instead of a bucket-level ACL.
# (UBLA is on, so this is the only way.)
resource "google_storage_bucket_iam_member" "public_read" {
  bucket = google_storage_bucket.images.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
