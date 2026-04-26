###############################################################################
# Network: a dedicated VPC with one subnet, plus a Serverless VPC Connector so
# Cloud Run can reach Cloud SQL through the private IP rather than the public
# internet (defence-in-depth + lower latency).
#
# Cloud SQL with private IP also requires a peering range reserved for Google
# services — that's the ``google_compute_global_address`` + the
# ``service_networking_connection`` below.
###############################################################################

resource "google_compute_network" "vpc" {
  name                    = "livemenu-vpc-${local.name_suffix}"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"

  depends_on = [google_project_service.enabled]
}

resource "google_compute_subnetwork" "subnet" {
  name                     = "livemenu-subnet-${local.name_suffix}"
  ip_cidr_range            = "10.20.0.0/24"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# /24 reserved for the Serverless VPC Connector.
resource "google_vpc_access_connector" "cloud_run" {
  name           = "lm-conn-${local.name_suffix}"
  region         = var.region
  network        = google_compute_network.vpc.name
  ip_cidr_range  = "10.30.0.0/28"
  min_throughput = 200
  max_throughput = 300

  depends_on = [google_project_service.enabled]
}

# Reserved range for Google managed services (Cloud SQL with private IP).
resource "google_compute_global_address" "private_services_range" {
  name          = "lm-psn-range-${local.name_suffix}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_services" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_services_range.name]
}
