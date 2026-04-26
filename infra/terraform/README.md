# LiveMenu — Terraform / IaC

Infrastructure-as-Code for the Entrega 2 deployment on Google Cloud Platform.

## What this provisions

| File | Resources |
|---|---|
| `apis.tf` | Project services (Run, Cloud SQL, Secret Manager, Storage, Cloud Build, Compute, KMS, etc.) |
| `network.tf` | VPC, regional subnet, Serverless VPC Connector, peering range for Cloud SQL |
| `iam.tf` | Three SAs (api, frontend, deployer) with least-privilege bindings |
| `secrets.tf` | `JWT_SECRET`, `IP_HASH_SALT`, `DB_PASSWORD` in Secret Manager + 40-day rotation schedule + Pub/Sub topic |
| `cloud_sql.tf` | Postgres 16 regional HA, daily backups (15-day retention), PITR, query insights, SSL-only, private IP |
| `storage.tf` | Images bucket — UBLA, versioning, lifecycle, public-read for menu images |
| `artifact_registry.tf` | Docker repo with retention policy |
| `cloud_run.tf` | API + Frontend, ingress restricted to the LB, secrets mounted at request time |
| `cloud_armor.tf` | OWASP top-10 preconfigured rules + rate limit + optional geo allow-list + adaptive DDoS |
| `load_balancer.tf` | Global external HTTPS LB, managed cert, modern SSL policy (TLS 1.2+), HTTP→HTTPS redirect, CDN on the SPA |
| `outputs.tf` | LB IP, Cloud SQL conn name, bucket name, AR repo path, deployer SA |