# CloudPulse

Open-source cloud cost management platform. Track, analyze, and optimize spending across **28 providers** — from AWS, Azure, and GCP to Datadog, Snowflake, OpenAI, and more.

## Features
- **Multi-Cloud Cost Dashboard** — unified view across all connected providers
- **28 Provider Integrations** — Cloud (AWS, Azure, GCP, Oracle, Linode), Kubernetes, Observability (Datadog, New Relic, Coralogix, Grafana Cloud), Databases (MongoDB, Snowflake, Databricks, PlanetScale, ClickHouse), AI/ML (OpenAI, Anthropic, Anyscale, Cursor), DevTools (GitHub, Temporal Cloud, Twilio), CDN (Fastly, Confluent, Cloudflare, Vercel), and Custom Providers via FOCUS spec
- **Anomaly Detection** — automatic spend spike alerts
- **Cost Recommendations** — find idle resources and optimization opportunities
- **Budgets & Segments** — set budgets, slice costs by team/environment/tag
- **Kubernetes Cost Allocation** — namespace and workload-level visibility
- **v2 REST API** — 69+ endpoints, token-based auth, DuckDB analytics engine
- **Reports** — shareable cost reports with token-based access

## Quick Start

```bash
git clone https://github.com/your-org/cloudpulse.git
cd cloudpulse

# Copy and edit environment variables
cp .env.example .env

# Start everything with Docker Compose
docker compose up -d --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Architecture

```
cloudpulse/
├── app/
│   ├── api/v2/             # FastAPI v2 endpoints (69+ routes)
│   ├── core/               # Config, auth, database
│   ├── models/             # SQLAlchemy models (28 providers)
│   ├── services/
│   │   ├── connectors/     # 28 provider connectors
│   │   ├── provider_registry.py  # Provider catalog
│   │   └── duckdb_engine.py      # Analytics engine
│   └── utils/
├── frontend/               # React + Vite (Tailwind CSS)
│   └── src/pages/Integrations.jsx  # Provider management UI
├── docker-compose.yml      # PostgreSQL + API + Frontend
├── LICENSE                 # Business Source License 1.1
└── CONTRIBUTING.md
```

**Stack**: FastAPI, SQLAlchemy (async), PostgreSQL, DuckDB, React, Vite, Tailwind CSS, Docker

## Integrations

Connect providers from the **Integrations** page or via the API:

```bash
# List available providers
curl http://localhost:8000/api/v2/integrations/catalog

# Connect a provider
curl -X POST http://localhost:8000/api/v2/integrations/connect \
  -H 'Content-Type: application/json' \
  -d '{"provider": "datadog", "credentials": {"api_key": "...", "app_key": "...", "site": "datadoghq.com"}}'
```

## License

This project is licensed under the [Business Source License 1.1](LICENSE).

- **Free for self-hosting** when your cloud spend is under $25k/month
- **Cannot be offered as a competing hosted service**
- Converts to **Apache 2.0** on 2029-02-17

See `LICENSE` for full terms.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CLA.md](CLA.md) before submitting.

All participants must follow our [Code of Conduct](CODE_OF_CONDUCT.md).
