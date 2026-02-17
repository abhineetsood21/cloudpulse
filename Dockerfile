FROM python:3.12-slim

WORKDIR /app

# System deps for asyncpg, DuckDB, and PyArrow
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create billing data directories for all supported providers
RUN mkdir -p /data/billing/aws /data/billing/gcp /data/billing/azure \
    /data/billing/oracle /data/billing/alibaba /data/billing/ibm \
    /data/billing/digitalocean /data/billing/snowflake /data/billing/databricks \
    /data/billing/datadog /data/billing/newrelic /data/billing/confluent \
    /data/billing/mongo-atlas /data/billing/elastic /data/billing/cloudflare

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
