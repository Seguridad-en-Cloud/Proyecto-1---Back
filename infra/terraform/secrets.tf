###############################################################################
# Secret Manager — Entrega 2 §3.2.
#
# Each sensitive value is stored as its own secret. The backend SA gets
# ``roles/secretmanager.secretAccessor`` on each one (per-secret IAM, no
# project-wide blanket access).
#
# Rotation: Secret Manager only delivers a Pub/Sub *notification* on the
# rotation period. The actual value swap is performed by an external rotator
# (e.g. a Cloud Function that reaches into Cloud SQL or a KMS-derived
# generator). For this delivery we configure the schedule + topic; the
# rotator function is documented but out of scope for the IaC here.
###############################################################################

# ── Topic that receives rotation events ──────────────────────────────────
resource "google_pubsub_topic" "secret_rotation" {
  name = "livemenu-secret-rotation-${local.name_suffix}"

  depends_on = [google_project_service.enabled]
}

# Grant Secret Manager's service agent permission to publish to the topic.
data "google_project" "current" {
  project_id = var.project_id
}

# Force-create the Secret Manager service identity. Just enabling the API
# does NOT create the agent service account — it only appears the first
# time the project consumes the API. Without this resource, the IAM binding
# below races and fails with "service account does not exist".
resource "google_project_service_identity" "secretmanager" {
  provider = google-beta
  project  = var.project_id
  service  = "secretmanager.googleapis.com"

  depends_on = [google_project_service.enabled]
}

resource "google_pubsub_topic_iam_member" "secretmanager_publisher" {
  topic  = google_pubsub_topic.secret_rotation.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_project_service_identity.secretmanager.email}"
}

# ── Helper: factory for "rotating" secrets ───────────────────────────────
locals {
  rotating_secrets = {
    JWT_SECRET = {
      description = "HS256 signing key for JWT access/refresh tokens"
    }
    IP_HASH_SALT = {
      description = "Salt for hashing client IPs in scan_events"
    }
    DB_PASSWORD = {
      description = "Password for the livemenu Cloud SQL user"
    }
  }
}

resource "google_secret_manager_secret" "rotating" {
  for_each = local.rotating_secrets

  secret_id = each.key

  labels = local.labels

  replication {
    auto {}
  }

  topics {
    name = google_pubsub_topic.secret_rotation.id
  }

  rotation {
    next_rotation_time = timeadd(timestamp(), "168h") # first rotation in 7 days
    rotation_period    = "${var.secret_rotation_seconds}s"
  }

  depends_on = [
    google_pubsub_topic_iam_member.secretmanager_publisher,
    google_project_service.enabled,
  ]

  # next_rotation_time uses ``timestamp()`` which would force replacement on
  # every plan. Ignore drift after the first apply.
  lifecycle {
    ignore_changes = [rotation[0].next_rotation_time]
  }
}

# ── Initial values ────────────────────────────────────────────────────────
# We seed every secret with a strong random value so the first ``terraform
# apply`` produces a runnable system. Operators (or the rotator) replace
# these with subsequent versions later.
resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "random_password" "ip_salt" {
  length  = 32
  special = false
}

resource "random_password" "db_password" {
  length      = 32
  special     = true
  min_lower   = 4
  min_upper   = 4
  min_numeric = 4
  min_special = 2
  override_special = "_-." # avoid characters that complicate dsn quoting
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.rotating["JWT_SECRET"].id
  secret_data = random_password.jwt_secret.result
}

resource "google_secret_manager_secret_version" "ip_salt" {
  secret      = google_secret_manager_secret.rotating["IP_HASH_SALT"].id
  secret_data = random_password.ip_salt.result
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.rotating["DB_PASSWORD"].id
  secret_data = random_password.db_password.result
}

# ── Per-secret IAM ────────────────────────────────────────────────────────
resource "google_secret_manager_secret_iam_member" "api_access" {
  for_each = google_secret_manager_secret.rotating

  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}
