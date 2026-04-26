###############################################################################
# Global external HTTPS Load Balancer fronting Cloud Armor + the two Cloud Run
# services.
#
# Routing:
#   * /api/*  → API service
#   * /m/*    → API service (public menu route)
#   * /docs, /openapi.json → API service (only used in non-prod)
#   * everything else → Frontend service
#
# Cert: Google-managed for var.domain_name when set; otherwise we still create
# the LB but skip the HTTPS proxy (you can attach a cert manually after
# pointing DNS).
###############################################################################

# Static external IP advertised in DNS.
resource "google_compute_global_address" "lb_ip" {
  name = "livemenu-lb-ip-${local.name_suffix}"
}

# ── Serverless network endpoint groups ────────────────────────────────────
resource "google_compute_region_network_endpoint_group" "api_neg" {
  provider              = google-beta
  name                  = "livemenu-api-neg-${local.name_suffix}"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.api.name
  }
}

resource "google_compute_region_network_endpoint_group" "frontend_neg" {
  provider              = google-beta
  name                  = "livemenu-front-neg-${local.name_suffix}"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.frontend.name
  }
}

# ── Backend services (carry Cloud Armor) ──────────────────────────────────
resource "google_compute_backend_service" "api" {
  name                            = "livemenu-api-bes-${local.name_suffix}"
  protocol                        = "HTTPS"
  load_balancing_scheme           = "EXTERNAL_MANAGED"
  enable_cdn                      = false
  security_policy                 = google_compute_security_policy.waf.id
  connection_draining_timeout_sec = 30

  backend {
    group = google_compute_region_network_endpoint_group.api_neg.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_backend_service" "frontend" {
  name                  = "livemenu-front-bes-${local.name_suffix}"
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  enable_cdn            = true # cache the static SPA bundle at the edge
  security_policy       = google_compute_security_policy.waf.id

  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    default_ttl       = 3600
    client_ttl        = 3600
    max_ttl           = 86400
    negative_caching  = true
    serve_while_stale = 86400
  }

  backend {
    group = google_compute_region_network_endpoint_group.frontend_neg.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# ── URL map ───────────────────────────────────────────────────────────────
resource "google_compute_url_map" "main" {
  name            = "livemenu-urlmap-${local.name_suffix}"
  default_service = google_compute_backend_service.frontend.id

  host_rule {
    hosts        = ["*"]
    path_matcher = "main"
  }

  path_matcher {
    name            = "main"
    default_service = google_compute_backend_service.frontend.id

    path_rule {
      paths   = ["/api", "/api/*", "/m", "/m/*", "/docs", "/redoc", "/openapi.json"]
      service = google_compute_backend_service.api.id
    }
  }
}

# ── Managed SSL certificate (only when a domain is configured) ────────────
resource "google_compute_managed_ssl_certificate" "main" {
  count = var.domain_name == "" ? 0 : 1

  name = "livemenu-cert-${local.name_suffix}"
  managed {
    domains = [var.domain_name]
  }
}

# ── HTTPS proxy + forwarding rule ─────────────────────────────────────────
resource "google_compute_target_https_proxy" "main" {
  count = var.domain_name == "" ? 0 : 1

  name             = "livemenu-https-proxy-${local.name_suffix}"
  url_map          = google_compute_url_map.main.id
  ssl_certificates = [google_compute_managed_ssl_certificate.main[0].id]
  # Block legacy ciphers; require modern TLS.
  ssl_policy = google_compute_ssl_policy.modern.id
}

resource "google_compute_global_forwarding_rule" "https" {
  count = var.domain_name == "" ? 0 : 1

  name                  = "livemenu-https-fr-${local.name_suffix}"
  target                = google_compute_target_https_proxy.main[0].id
  port_range            = "443"
  ip_address            = google_compute_global_address.lb_ip.address
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# ── HTTP → HTTPS redirect ─────────────────────────────────────────────────
resource "google_compute_url_map" "http_redirect" {
  count = var.domain_name == "" ? 0 : 1

  name = "livemenu-http-redirect-${local.name_suffix}"
  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

resource "google_compute_target_http_proxy" "http_redirect" {
  count = var.domain_name == "" ? 0 : 1

  name    = "livemenu-http-proxy-${local.name_suffix}"
  url_map = google_compute_url_map.http_redirect[0].id
}

resource "google_compute_global_forwarding_rule" "http" {
  count = var.domain_name == "" ? 0 : 1

  name                  = "livemenu-http-fr-${local.name_suffix}"
  target                = google_compute_target_http_proxy.http_redirect[0].id
  port_range            = "80"
  ip_address            = google_compute_global_address.lb_ip.address
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# ── Modern TLS policy: TLS 1.2+, MODERN profile (no RC4, no SHA1) ─────────
resource "google_compute_ssl_policy" "modern" {
  name            = "livemenu-tls-modern-${local.name_suffix}"
  profile         = "MODERN"
  min_tls_version = "TLS_1_2"
}
