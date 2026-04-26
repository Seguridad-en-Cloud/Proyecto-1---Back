###############################################################################
# Provider + backend wiring.
#
# State is kept in a GCS bucket so the team can collaborate. The bucket itself
# is bootstrapped manually once (see README.md) — Terraform cannot create the
# bucket that holds its own state.
###############################################################################

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.40"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.40"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "gcs" {
     bucket = "livemenu-tfstate-lvm"
     prefix = "entrega-2"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Common labels applied to every resource that supports them. Useful for cost
# allocation in Billing reports and for filtering in Cloud Logging.
locals {
  labels = {
    project     = "livemenu"
    course      = "msin4215"
    delivery    = "entrega-2"
    environment = var.environment
    managed-by  = "terraform"
  }

  # Short, deterministic suffix so multiple students can share a project
  # without colliding on globally-unique names (buckets, registries…).
  name_suffix = var.name_suffix
}
