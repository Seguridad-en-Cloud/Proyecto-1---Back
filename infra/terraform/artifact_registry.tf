###############################################################################
# Artifact Registry: Docker repository for the API and frontend images.
#
# A single repository is fine — paths inside the repo separate the artifacts:
#   <region>-docker.pkg.dev/<project>/livemenu-<suffix>/api:<tag>
#   <region>-docker.pkg.dev/<project>/livemenu-<suffix>/frontend:<tag>
#
# Vulnerability scanning is enabled at the project level by Container
# Analysis (free for the first 10 images/month per repo). Trivy in CI/CD
# provides a second, gating scan before deployment.
###############################################################################

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "livemenu-${local.name_suffix}"
  description   = "Container images for LiveMenu API & frontend"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-recent-tagged"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }

  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "604800s" # 7 days
    }
  }

  labels = local.labels

  depends_on = [google_project_service.enabled]
}
