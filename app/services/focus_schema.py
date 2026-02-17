"""
FOCUS Schema — FinOps Open Cost & Usage Specification

Normalizes billing data from multiple cloud providers into a unified schema.
This allows CloudPulse to query AWS, GCP, and Azure cost data with the same
SQL regardless of the source.

FOCUS spec: https://focus.finops.org/

Unified columns:
    provider        - 'aws', 'gcp', 'azure'
    account_id      - Cloud account/project/subscription ID
    service         - Service name (e.g., 'Amazon EC2', 'Compute Engine')
    region          - Region identifier
    resource_id     - Resource ARN/ID
    usage_date      - Date of usage (DATE type)
    charge_type     - 'Usage', 'Tax', 'Credit', 'Refund', 'Support', etc.
    amount          - Cost amount (DOUBLE)
    currency        - Currency code (e.g., 'USD')
    tags            - JSON object of resource tags
"""

import logging
from typing import Optional

import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


# --- FOCUS output schema ---

FOCUS_SCHEMA = pa.schema([
    pa.field("provider", pa.string(), nullable=False),
    pa.field("account_id", pa.string(), nullable=False),
    pa.field("service", pa.string(), nullable=False),
    pa.field("region", pa.string(), nullable=True),
    pa.field("resource_id", pa.string(), nullable=True),
    pa.field("usage_date", pa.date32(), nullable=False),
    pa.field("charge_type", pa.string(), nullable=True),
    pa.field("amount", pa.float64(), nullable=False),
    pa.field("currency", pa.string(), nullable=False),
    pa.field("tags", pa.string(), nullable=True),  # JSON string
])


# --- AWS CUR Column Mapping ---

# AWS CUR has hundreds of columns. These are the critical ones we map to FOCUS.
AWS_CUR_COLUMN_MAP = {
    "lineItem/UsageAccountId": "account_id",
    "lineItem/ProductCode": "service",
    "product/region": "region",
    "lineItem/ResourceId": "resource_id",
    "lineItem/UsageStartDate": "usage_date",
    "lineItem/LineItemType": "charge_type",
    "lineItem/UnblendedCost": "amount",
    "lineItem/CurrencyCode": "currency",
}

# CUR charge type normalization
AWS_CHARGE_TYPE_MAP = {
    "Usage": "Usage",
    "Tax": "Tax",
    "Credit": "Credit",
    "Refund": "Refund",
    "Fee": "Fee",
    "RIFee": "Commitment",
    "SavingsPlanCoveredUsage": "Usage",
    "SavingsPlanNegation": "Credit",
    "SavingsPlanUpfrontFee": "Commitment",
    "SavingsPlanRecurringFee": "Commitment",
    "DiscountedUsage": "Usage",
    "EdpDiscount": "Credit",
    "BundledDiscount": "Credit",
}

# CUR product code to friendly service name
AWS_SERVICE_NAME_MAP = {
    "AmazonEC2": "Amazon EC2",
    "AmazonS3": "Amazon S3",
    "AmazonRDS": "Amazon RDS",
    "AWSLambda": "AWS Lambda",
    "AmazonDynamoDB": "Amazon DynamoDB",
    "AmazonCloudFront": "Amazon CloudFront",
    "AmazonEKS": "Amazon EKS",
    "AmazonElastiCache": "Amazon ElastiCache",
    "AmazonRedshift": "Amazon Redshift",
    "AmazonSNS": "Amazon SNS",
    "AmazonSQS": "Amazon SQS",
    "AmazonKinesis": "Amazon Kinesis",
    "AWSCloudTrail": "AWS CloudTrail",
    "AmazonGuardDuty": "Amazon GuardDuty",
    "AWSConfig": "AWS Config",
    "AmazonRoute53": "Amazon Route 53",
    "AmazonVPC": "Amazon VPC",
    "AWSELB": "Elastic Load Balancing",
    "AmazonECS": "Amazon ECS",
    "AmazonEFS": "Amazon EFS",
    "AmazonOpenSearchService": "Amazon OpenSearch",
    "AmazonSageMaker": "Amazon SageMaker",
}


# --- GCP Billing Export Column Mapping ---

GCP_COLUMN_MAP = {
    "project.id": "account_id",
    "service.description": "service",
    "location.region": "region",
    "resource.name": "resource_id",
    "usage_start_time": "usage_date",
    "cost_type": "charge_type",
    "cost": "amount",
    "currency": "currency",
}

GCP_CHARGE_TYPE_MAP = {
    "regular": "Usage",
    "tax": "Tax",
    "adjustment": "Credit",
    "rounding_error": "Credit",
}


# --- Azure Cost Management Export Column Mapping ---

AZURE_COLUMN_MAP = {
    "SubscriptionId": "account_id",
    "MeterCategory": "service",
    "ResourceLocation": "region",
    "ResourceId": "resource_id",
    "Date": "usage_date",
    "ChargeType": "charge_type",
    "CostInBillingCurrency": "amount",
    "BillingCurrency": "currency",
}

AZURE_CHARGE_TYPE_MAP = {
    "Usage": "Usage",
    "Purchase": "Commitment",
    "Tax": "Tax",
    "UnusedReservation": "Credit",
    "Refund": "Refund",
}


def normalize_aws_cur(rows: list[dict]) -> list[dict]:
    """
    Normalize AWS CUR rows to FOCUS schema.

    Args:
        rows: List of dicts from CUR CSV/Parquet with original AWS column names.

    Returns:
        List of FOCUS-normalized dicts ready for Parquet writing.
    """
    normalized = []
    for row in rows:
        amount_raw = row.get("lineItem/UnblendedCost", "0")
        try:
            amount = float(amount_raw)
        except (ValueError, TypeError):
            amount = 0.0

        if abs(amount) < 0.0001:
            continue

        # Normalize charge type
        raw_charge_type = row.get("lineItem/LineItemType", "Usage")
        charge_type = AWS_CHARGE_TYPE_MAP.get(raw_charge_type, "Usage")

        # Normalize service name
        raw_service = row.get("lineItem/ProductCode", "Unknown")
        service = AWS_SERVICE_NAME_MAP.get(raw_service, raw_service)

        # Extract usage date (CUR provides full timestamp)
        usage_date_raw = row.get("lineItem/UsageStartDate", "")
        usage_date = usage_date_raw[:10] if usage_date_raw else None
        if not usage_date:
            continue

        # Extract tags — CUR tag columns have prefix "resourceTags/user:"
        tags = {}
        for key, value in row.items():
            if key.startswith("resourceTags/user:") and value:
                tag_key = key.replace("resourceTags/user:", "")
                tags[tag_key] = value

        import json
        normalized.append({
            "provider": "aws",
            "account_id": row.get("lineItem/UsageAccountId", ""),
            "service": service,
            "region": row.get("product/region", ""),
            "resource_id": row.get("lineItem/ResourceId", ""),
            "usage_date": usage_date,
            "charge_type": charge_type,
            "amount": round(amount, 6),
            "currency": row.get("lineItem/CurrencyCode", "USD"),
            "tags": json.dumps(tags) if tags else None,
        })

    logger.info(f"Normalized {len(normalized)} AWS CUR rows to FOCUS schema")
    return normalized


def normalize_gcp_export(rows: list[dict]) -> list[dict]:
    """
    Normalize GCP BigQuery billing export rows to FOCUS schema.

    Args:
        rows: List of dicts from GCP billing export query.

    Returns:
        List of FOCUS-normalized dicts.
    """
    import json

    normalized = []
    for row in rows:
        amount_raw = row.get("cost", 0)
        try:
            amount = float(amount_raw)
        except (ValueError, TypeError):
            amount = 0.0

        if abs(amount) < 0.0001:
            continue

        raw_charge_type = row.get("cost_type", "regular")
        charge_type = GCP_CHARGE_TYPE_MAP.get(raw_charge_type, "Usage")

        usage_date_raw = row.get("usage_start_time", "")
        if hasattr(usage_date_raw, "strftime"):
            usage_date = usage_date_raw.strftime("%Y-%m-%d")
        else:
            usage_date = str(usage_date_raw)[:10]

        if not usage_date:
            continue

        # GCP labels
        labels = row.get("labels", [])
        tags = {}
        if isinstance(labels, list):
            for label in labels:
                if isinstance(label, dict):
                    tags[label.get("key", "")] = label.get("value", "")
        elif isinstance(labels, dict):
            tags = labels

        normalized.append({
            "provider": "gcp",
            "account_id": row.get("project.id", row.get("project_id", "")),
            "service": row.get("service.description", row.get("service_description", "Unknown")),
            "region": row.get("location.region", row.get("location_region", "")),
            "resource_id": row.get("resource.name", row.get("resource_name", "")),
            "usage_date": usage_date,
            "charge_type": charge_type,
            "amount": round(amount, 6),
            "currency": row.get("currency", "USD"),
            "tags": json.dumps(tags) if tags else None,
        })

    logger.info(f"Normalized {len(normalized)} GCP billing rows to FOCUS schema")
    return normalized


def normalize_azure_export(rows: list[dict]) -> list[dict]:
    """
    Normalize Azure Cost Management export rows to FOCUS schema.

    Args:
        rows: List of dicts from Azure cost export CSV.

    Returns:
        List of FOCUS-normalized dicts.
    """
    import json

    normalized = []
    for row in rows:
        amount_raw = row.get("CostInBillingCurrency", row.get("Cost", 0))
        try:
            amount = float(amount_raw)
        except (ValueError, TypeError):
            amount = 0.0

        if abs(amount) < 0.0001:
            continue

        raw_charge_type = row.get("ChargeType", "Usage")
        charge_type = AZURE_CHARGE_TYPE_MAP.get(raw_charge_type, "Usage")

        usage_date_raw = row.get("Date", row.get("UsageDateTime", ""))
        if hasattr(usage_date_raw, "strftime"):
            usage_date = usage_date_raw.strftime("%Y-%m-%d")
        else:
            usage_date = str(usage_date_raw)[:10]

        if not usage_date:
            continue

        # Azure tags come as JSON string or dict
        raw_tags = row.get("Tags", row.get("tags", ""))
        tags = {}
        if isinstance(raw_tags, dict):
            tags = raw_tags
        elif isinstance(raw_tags, str) and raw_tags:
            try:
                tags = json.loads(raw_tags)
            except json.JSONDecodeError:
                pass

        normalized.append({
            "provider": "azure",
            "account_id": row.get("SubscriptionId", row.get("SubscriptionGuid", "")),
            "service": row.get("MeterCategory", row.get("ServiceName", "Unknown")),
            "region": row.get("ResourceLocation", row.get("ResourceRegion", "")),
            "resource_id": row.get("ResourceId", row.get("InstanceId", "")),
            "usage_date": usage_date,
            "charge_type": charge_type,
            "amount": round(amount, 6),
            "currency": row.get("BillingCurrency", row.get("Currency", "USD")),
            "tags": json.dumps(tags) if tags else None,
        })

    logger.info(f"Normalized {len(normalized)} Azure cost rows to FOCUS schema")
    return normalized


def write_focus_parquet(rows: list[dict], output_path: str):
    """
    Write FOCUS-normalized rows to a Parquet file.

    Args:
        rows: List of FOCUS-schema dicts.
        output_path: Path to write the .parquet file.
    """
    import json
    from datetime import date as date_type

    if not rows:
        logger.warning("No rows to write — skipping Parquet output")
        return

    # Build columnar arrays
    providers = []
    account_ids = []
    services = []
    regions = []
    resource_ids = []
    usage_dates = []
    charge_types = []
    amounts = []
    currencies = []
    tags_col = []

    for row in rows:
        providers.append(row["provider"])
        account_ids.append(row["account_id"])
        services.append(row["service"])
        regions.append(row.get("region"))
        resource_ids.append(row.get("resource_id"))

        # Parse date
        ud = row["usage_date"]
        if isinstance(ud, str):
            from datetime import datetime
            ud = datetime.strptime(ud, "%Y-%m-%d").date()
        usage_dates.append(ud)

        charge_types.append(row.get("charge_type"))
        amounts.append(float(row["amount"]))
        currencies.append(row["currency"])
        tags_col.append(row.get("tags"))

    table = pa.table({
        "provider": pa.array(providers, type=pa.string()),
        "account_id": pa.array(account_ids, type=pa.string()),
        "service": pa.array(services, type=pa.string()),
        "region": pa.array(regions, type=pa.string()),
        "resource_id": pa.array(resource_ids, type=pa.string()),
        "usage_date": pa.array(usage_dates, type=pa.date32()),
        "charge_type": pa.array(charge_types, type=pa.string()),
        "amount": pa.array(amounts, type=pa.float64()),
        "currency": pa.array(currencies, type=pa.string()),
        "tags": pa.array(tags_col, type=pa.string()),
    })

    from pathlib import Path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, output_path, compression="snappy")
    logger.info(f"Wrote {len(rows)} FOCUS rows to {output_path}")
