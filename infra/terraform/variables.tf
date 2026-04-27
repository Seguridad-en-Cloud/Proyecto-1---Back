variable "project_id" {
  description = "GCP project ID where everything will be deployed."
  type        = string
}

variable "region" {
  description = "Primary region (Cloud Run, Cloud SQL, GCS regional bucket)."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment tag (dev|staging|prod). Used in labels only."
  type        = string
  default     = "prod"
}

variable "name_suffix" {
  description = <<EOT
Short suffix appended to globally-unique resource names (e.g. GCS buckets,
Artifact Registry repos). Use 4–6 chars, e.g. your team initials.
EOT
  type        = string
  validation {
    condition     = length(var.name_suffix) >= 3 && length(var.name_suffix) <= 8
    error_message = "name_suffix must be 3–8 characters."
  }
}

variable "domain_name" {
  description = <<EOT
Fully-qualified domain to attach to the HTTPS load balancer (e.g. livemenu.example.com).
A managed Google certificate will be provisioned for it. Leave empty to use
a sslip.io / nip.io domain derived from the LB IP for testing.
EOT
  type        = string
  default     = "live-menu-cloud-sec.34.96.107.81.sslip.io"
}

variable "db_tier" {
  description = "Cloud SQL machine type. db-custom-1-3840 = 1 vCPU / 3.75 GiB."
  type        = string
  default     = "db-custom-1-3840"
}

variable "db_disk_size_gb" {
  description = "Initial Cloud SQL disk size (GB). Auto-resizes upward."
  type        = number
  default     = 20
}

variable "db_backup_retention_days" {
  description = "Days of automated backups retained. Entrega 2 requires ≥ 15."
  type        = number
  default     = 15
  validation {
    condition     = var.db_backup_retention_days >= 15
    error_message = "Entrega 2 requires backup retention of at least 15 days."
  }
}

variable "secret_rotation_seconds" {
  description = "Rotation period in seconds. Entrega 2 requires ≤ 40 days."
  type        = number
  default     = 3456000 # 40 days
  validation {
    condition     = var.secret_rotation_seconds <= 3456000
    error_message = "Rotation period must be at most 40 days (3 456 000 s)."
  }
}

variable "allowed_geo_codes" {
  description = <<EOT
ISO-3166 country codes allowed by Cloud Armor. Empty = no geo-filtering.
Example: ["CO", "US", "MX"].
EOT
  type        = list(string)
  default     = []
}

variable "rate_limit_rpm_per_ip" {
  description = "Requests per minute per IP enforced by Cloud Armor."
  type        = number
  default     = 600
}

variable "image_tag" {
  description = <<EOT
Tag to deploy from Artifact Registry. CI overwrites this with the commit SHA;
you can pin to "latest" for manual applies after a successful pipeline run.
EOT
  type        = string
  default     = "latest"
}

variable "cors_origins" {
  description = "Comma-separated list of origins allowed by the API."
  type        = string
  default     = "https://live-menu-cloud-sec.34.96.107.81.sslip.io"
}
