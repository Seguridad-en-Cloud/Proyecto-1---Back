###############################################################################
# Cloud Armor security policy attached to the global LB.
#
# Coverage of Entrega 2 §6 (WAF):
#   * OWASP Top-10 preconfigured rules: SQLi, XSS, RCE, LFI, RFI, scannerdetection,
#     protocolattack, sessionfixation. Sensitivity = 1 (default tuning).
#   * Per-IP rate limit (configurable; default 600 rpm).
#   * Geo allow-list (optional, controlled by var.allowed_geo_codes).
#   * Default deny? No — default action is "allow"; we deny what matches a
#     ruleset. The Internet-facing menu must remain reachable to anyone.
###############################################################################

resource "google_compute_security_policy" "waf" {
  name        = "livemenu-waf-${local.name_suffix}"
  description = "OWASP Top 10 + rate limit for the LiveMenu LB"
  type        = "CLOUD_ARMOR"

  # ── 1000-1099 — OWASP Top 10 preconfigured rules ──────────────────────
  rule {
    action   = "deny(403)"
    priority = 1000
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 1}) && !request.path.matches('/api/v1/admin/upload')"
      }
    }
    description = "OWASP A03:2021 Injection — SQLi"
  }

  rule {
    action   = "deny(403)"
    priority = 1010
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('xss-v33-stable', {'sensitivity': 1}) && !request.path.matches('/api/v1/admin/upload')"
      }
    }
    description = "OWASP A03:2021 Injection — XSS"
  }

  rule {
    action   = "deny(403)"
    priority = 1020
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('lfi-v33-stable', {'sensitivity': 1})"
      }
    }
    description = "Local file inclusion"
  }

  rule {
    action   = "deny(403)"
    priority = 1030
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('rfi-v33-stable', {'sensitivity': 1})"
      }
    }
    description = "Remote file inclusion"
  }

  rule {
    action   = "deny(403)"
    priority = 1040
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('rce-v33-stable', {'sensitivity': 1}) && !request.path.matches('/api/v1/admin/upload')"
      }
    }
    description = "Remote code execution"
  }

  rule {
    action   = "deny(403)"
    priority = 1050
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('scannerdetection-v33-stable', {'sensitivity': 1})"
      }
    }
    description = "Vulnerability scanners"
  }

  rule {
    action   = "deny(403)"
    priority = 1060
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('protocolattack-v33-stable', {'sensitivity': 1}) && !request.path.matches('/api/v1/admin/upload')"
      }
    }
    description = "HTTP protocol attacks"
  }

  rule {
    action   = "deny(403)"
    priority = 1070
    match {
      expr {
        expression = "evaluatePreconfiguredWaf('sessionfixation-v33-stable', {'sensitivity': 1})"
      }
    }
    description = "Session fixation"
  }

  # ── 1500 — Throttle: per-IP rate limit ────────────────────────────────
  rule {
    action   = "throttle"
    priority = 1500
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = var.rate_limit_rpm_per_ip
        interval_sec = 60
      }
    }
    description = "Layer-7 rate limit complementing the API's slowapi middleware"
  }

  # ── 2000 — Optional geo allow-list ────────────────────────────────────
  # Active only when allowed_geo_codes is non-empty. Denies traffic *not*
  # matching the configured countries.
  dynamic "rule" {
    for_each = length(var.allowed_geo_codes) > 0 ? [1] : []
    content {
      action   = "deny(403)"
      priority = 2000
      match {
        expr {
          expression = "!(${join(" || ", [for c in var.allowed_geo_codes : "origin.region_code == '${c}'"])})"
        }
      }
      description = "Geo allow-list (var.allowed_geo_codes)"
    }
  }

  # ── 2147483647 — Default rule (built-in priority, must be allow) ──────
  rule {
    action   = "allow"
    priority = 2147483647
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow (overridden by deny rules above)"
  }

  adaptive_protection_config {
    layer_7_ddos_defense_config {
      enable          = true
      rule_visibility = "STANDARD"
    }
  }
}
