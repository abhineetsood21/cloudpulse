# Self-Hosting CloudPulse

Deploy CloudPulse on your own infrastructure with Docker Compose.

## Prerequisites

| Requirement | Minimum |
|---|---|
| Docker Engine | 24+ |
| Docker Compose | v2.20+ |
| RAM | 2 GB |
| Disk | 10 GB (more for billing data) |

Optional — to ingest real billing data you will need credentials for one or more cloud providers (see **Cloud Provider Setup** below).

## Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/cloudpulse.git
cd cloudpulse

# Create an environment file
cp .env.example .env   # then edit .env — see "Configuration" below

# Launch everything
docker compose up -d
```

CloudPulse is now available at:

- **Frontend** — http://localhost:3000
- **API** — http://localhost:8000
- **API docs** — http://localhost:8000/docs

## Configuration

All configuration is done via environment variables. Create a `.env` file in the project root (Docker Compose reads it automatically).

### Required Variables

```
POSTGRES_PASSWORD=<strong-random-password>
APP_SECRET_KEY=<random-string-for-sessions>
JWT_SECRET_KEY=<random-string-for-jwt>
```

### AWS (optional)

```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
CUR_S3_BUCKET=your-cur-bucket
CUR_S3_PREFIX=reports/cloudpulse
CUR_REPORT_NAME=cloudpulse-cur
```

The IAM user/role needs at minimum:
- `s3:GetObject` / `s3:ListBucket` on the CUR bucket
- `ce:GetCostAndUsage` for the commitment analyzer
- `ec2:Describe*`, `rds:Describe*`, `elasticloadbalancing:Describe*` for recommendations

### GCP (optional)

```
GCP_CREDENTIALS_JSON=/path/to/service-account.json
GCP_BILLING_TABLE=project.dataset.gcp_billing_export_v1_XXXXXX
```

### Azure (optional)

```
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_STORAGE_ACCOUNT=billingexports
AZURE_STORAGE_CONTAINER=exports
```

## Architecture

```
┌───────────┐      ┌───────────┐      ┌────────────┐
│  Frontend │─────▶│  API      │─────▶│ PostgreSQL │
│  (nginx)  │ :80  │ (FastAPI) │ :8000│            │
└───────────┘      │           │      └────────────┘
                   │  DuckDB   │
                   │ (embedded)│
                   └───────────┘
```

- **Frontend** — React SPA served by nginx, proxies `/api/` to the backend.
- **API** — FastAPI. Handles auth, CRUD, CQL queries, recommendations.
- **DuckDB** — Embedded OLAP engine. Reads Parquet files from the billing data volume.
- **PostgreSQL** — Stores users, workspaces, dashboards, reports, and other metadata.

## Data Persistence

Two Docker volumes are created:

- `pgdata` — PostgreSQL data directory.
- `billing_data` — DuckDB database file + Parquet billing exports (`/data/`).

**Back up both volumes** to avoid data loss:

```bash
# Example: tar backup of billing data
docker run --rm -v cloudpulse_billing_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/billing_data_backup.tar.gz -C /data .
```

## Ingesting Billing Data

### AWS CUR

1. Enable CUR in the AWS Billing console (Parquet format recommended).
2. Set `CUR_S3_BUCKET`, `CUR_S3_PREFIX`, and `CUR_REPORT_NAME` in `.env`.
3. Add a cloud account via the API or UI, then trigger a sync:

```bash
curl -X POST http://localhost:8000/api/v2/cloud_accounts \
  -H "Content-Type: application/json" \
  -d '{"provider":"aws","name":"Production","connection_config":{}}'
```

### GCP / Azure

Follow the same flow — create a cloud account with the appropriate provider and trigger a sync. The connectors will pull data from BigQuery (GCP) or Blob Storage (Azure).

### Local CSV (development)

Place CSV files in `data/billing/aws/` on the host (mounted into the container at `/data/billing/aws/`). The CUR ingestor will pick them up.

## Upgrading

```bash
git pull
docker compose build
docker compose up -d
```

Database migrations (if any) run automatically on API startup via Alembic.

## Troubleshooting

### Containers won't start

```bash
docker compose logs api       # check backend logs
docker compose logs postgres  # check DB logs
```

### API returns 500 errors

- Ensure `DATABASE_URL` matches the Postgres credentials.
- Check that the `postgres` container is healthy: `docker compose ps`.

### Frontend shows blank page

- Confirm the API container is running — nginx proxies `/api/` to it.
- Check browser console for network errors.

## Security Recommendations

- **Change all default secrets** in `.env` before deploying.
- Place an HTTPS reverse proxy (e.g. Caddy, Traefik, or an ALB) in front of the frontend.
- Restrict Postgres port (`5432`) to internal networks only; remove the port mapping in `docker-compose.yml` if external access is not needed.
- Rotate cloud provider credentials regularly and use scoped IAM policies.

## Kubernetes Deployment

For production Kubernetes deployments, see the Helm chart in `tools/cloudpulse-helm-charts/`. Update `values.yaml` with your image registry and configuration, then:

```bash
helm install cloudpulse ./tools/cloudpulse-helm-charts -n cloudpulse --create-namespace
```
