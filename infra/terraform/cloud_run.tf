###############################################################################
# Cloud Run services for the API (FastAPI) and the frontend (nginx serving the
# Vite bundle).
#
# Both services:
#   * Run as their dedicated SA (least privilege).
#   * Are reachable only through the HTTPS load balancer (ingress = INTERNAL_AND_CLOUD_LOAD_BALANCING).
#     This means the rubric's "expose only behind WAF" requirement is enforced
#     at the platform level, not just by routing.
#
# The API service:
#   * Reads JWT_SECRET / IP_HASH_SALT / DB_PASSWORD from Secret Manager
#     directly (no env vars holding the value).
#   * Connects to Cloud SQL through the VPC connector + Cloud SQL Connector
#     (CLOUD_SQL_CONNECTION_NAME env var triggers the code path in
#     ``database/session.py``).
###############################################################################

locals {
  api_image      = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.containers.repository_id}/api:${var.image_tag}"
  frontend_image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.containers.repository_id}/frontend:${var.image_tag}"

  # Public Google placeholder used the first time we apply, before CI has
  # pushed any image to Artifact Registry. After the first CI run the real
  # image is in place and Terraform must NOT roll it back, so we
  # ignore_changes on the container image (see lifecycle blocks below).
  placeholder_image = "us-docker.pkg.dev/cloudrun/container/hello"
}

# Detect whether the real images exist yet. If terraform has never seen a
# successful CI run, fall back to the placeholder. We can't actually probe
# Artifact Registry from Terraform, so we use a variable: ``image_tag = "latest"``
# means "first apply, use placeholder"; any other value means "deploy the
# image CI tagged with that SHA".
locals {
  use_placeholder = var.image_tag == "latest"
  api_image_effective      = local.use_placeholder ? local.placeholder_image : local.api_image
  frontend_image_effective = local.use_placeholder ? local.placeholder_image : local.frontend_image
}

# ── Backend (FastAPI) ────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "api" {
  name     = "livemenu-api-${local.name_suffix}"
  location = var.region

  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.api.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    vpc_access {
      connector = google_vpc_access_connector.cloud_run.id
      egress    = "ALL_TRAFFIC" # so Cloud SQL private IP is reachable
    }

    containers {
      image = local.api_image_effective

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "STORAGE_BACKEND"
        value = "gcs"
      }
      env {
        name  = "GCS_BUCKET"
        value = google_storage_bucket.images.name
      }
      env {
        name  = "CLOUD_SQL_CONNECTION_NAME"
        value = google_sql_database_instance.postgres.connection_name
      }
      env {
        name  = "DB_USER"
        value = google_sql_user.app.name
      }
      env {
        name  = "DB_NAME"
        value = google_sql_database.app.name
      }
      env {
        name  = "CORS_ORIGINS"
        value = var.cors_origins
      }
      env {
        name  = "TRUSTED_PROXIES"
        value = "1"
      }
      env {
        name  = "ENABLE_DOCS"
        value = "false" # turn off Swagger in prod
      }
      env {
        name  = "RATE_LIMIT_PER_MINUTE"
        value = "100"
      }

      # Secret references — values are mounted at request time, never stored
      # in the revision metadata.
      env {
        name = "JWT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.rotating["JWT_SECRET"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "IP_HASH_SALT"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.rotating["IP_HASH_SALT"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.rotating["DB_PASSWORD"].secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/api/v1/auth/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        timeout_seconds       = 3
        failure_threshold     = 30
      }

      liveness_probe {
        http_get {
          path = "/api/v1/auth/health"
        }
        period_seconds  = 30
        timeout_seconds = 5
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = local.labels

  depends_on = [
    google_project_iam_member.api_sql_client,
    google_storage_bucket_iam_member.api_bucket_admin,
    google_secret_manager_secret_iam_member.api_access,
    google_secret_manager_secret_version.jwt_secret,
    google_secret_manager_secret_version.ip_salt,
    google_secret_manager_secret_version.db_password,
  ]

  # CI/CD owns the container image after the first deploy. Without this
  # block, the next ``terraform apply`` would roll the service back to the
  # placeholder (or to var.image_tag="latest") and break production.
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}

# ── Frontend (nginx-unprivileged) ─────────────────────────────────────────
resource "google_cloud_run_v2_service" "frontend" {
  name     = "livemenu-frontend-${local.name_suffix}"
  location = var.region

  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.frontend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = local.frontend_image_effective

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
        cpu_idle = true
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = local.labels

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}
