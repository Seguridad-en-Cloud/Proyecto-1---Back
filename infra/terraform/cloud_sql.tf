###############################################################################
# Cloud SQL — PostgreSQL 16 with regional HA, daily backups (≥ 15 days
# retention), Google-managed encryption at rest, and a private IP that's only
# reachable through the VPC connector.
###############################################################################

resource "google_sql_database_instance" "postgres" {
  name             = "livemenu-pg-${local.name_suffix}"
  database_version = "POSTGRES_16"
  region           = var.region

  deletion_protection = true

  depends_on = [
    google_service_networking_connection.private_services,
    google_project_service.enabled,
  ]

  settings {
    tier              = var.db_tier
    edition           = "ENTERPRISE"
    availability_type = "REGIONAL" # Multi-AZ
    disk_size         = var.db_disk_size_gb
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    user_labels = local.labels

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.vpc.id
      enable_private_path_for_google_cloud_services = true
      ssl_mode                                      = "ENCRYPTED_ONLY"
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      location                       = var.region

      backup_retention_settings {
        retained_backups = var.db_backup_retention_days
        retention_unit   = "COUNT"
      }
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 4
      update_track = "stable"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    database_flags {
      name  = "log_min_duration_statement"
      value = "500" # log slow queries (>500ms)
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = false # privacy: never log client IPs
    }
  }
}

resource "google_sql_database" "app" {
  name     = "livemenu"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = "livemenu"
  instance = google_sql_database_instance.postgres.name
  password = google_secret_manager_secret_version.db_password.secret_data
}
