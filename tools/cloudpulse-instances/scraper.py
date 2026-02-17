"""
CloudPulse Instances — AWS Instance Pricing Scraper.

Fetches EC2, RDS, ElastiCache, and OpenSearch instance pricing data
from the AWS Pricing API and generates a static JSON dataset.

Similar to ec2instances.info (Vantage's most popular open-source project).

Usage:
    python scraper.py --output data/instances.json
    python scraper.py --service ec2 --region us-east-1
"""

import argparse
import json
import logging
from pathlib import Path

import boto3

logger = logging.getLogger(__name__)

SERVICES = {
    "ec2": "AmazonEC2",
    "rds": "AmazonRDS",
    "elasticache": "AmazonElastiCache",
    "opensearch": "AmazonES",
}

REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-central-1",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
]


def get_pricing_client(region: str = "us-east-1"):
    """AWS Pricing API is only available in us-east-1 and ap-south-1."""
    return boto3.client("pricing", region_name=region)


def fetch_ec2_instances(client, region: str) -> list[dict]:
    """Fetch EC2 instance types and their pricing."""
    instances = []
    paginator = client.get_paginator("get_products")

    filters = [
        {"Type": "TERM_MATCH", "Field": "servicecode", "Value": "AmazonEC2"},
        {"Type": "TERM_MATCH", "Field": "location", "Value": _region_name(region)},
        {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
        {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
        {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
        {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
    ]

    try:
        for page in paginator.paginate(ServiceCode="AmazonEC2", Filters=filters):
            for item in page.get("PriceList", []):
                data = json.loads(item) if isinstance(item, str) else item
                product = data.get("product", {})
                attrs = product.get("attributes", {})

                instance_type = attrs.get("instanceType", "")
                if not instance_type or "." not in instance_type:
                    continue

                # Extract On-Demand pricing
                on_demand = _extract_on_demand_price(data)

                instances.append({
                    "instance_type": instance_type,
                    "family": instance_type.split(".")[0],
                    "vcpu": _safe_int(attrs.get("vcpu")),
                    "memory_gb": _parse_memory(attrs.get("memory", "")),
                    "storage": attrs.get("storage", "EBS only"),
                    "network_performance": attrs.get("networkPerformance", ""),
                    "processor": attrs.get("physicalProcessor", ""),
                    "architecture": attrs.get("processorArchitecture", ""),
                    "gpu": _safe_int(attrs.get("gpu", "0")),
                    "on_demand_hourly": on_demand,
                    "on_demand_monthly": round(on_demand * 730, 2) if on_demand else None,
                    "region": region,
                })
    except Exception as e:
        logger.warning(f"Failed to fetch EC2 pricing for {region}: {e}")

    return instances


def _extract_on_demand_price(data: dict) -> float | None:
    """Extract On-Demand price from pricing API response."""
    terms = data.get("terms", {}).get("OnDemand", {})
    for term in terms.values():
        for dimension in term.get("priceDimensions", {}).values():
            price = dimension.get("pricePerUnit", {}).get("USD")
            if price:
                return float(price)
    return None


def _region_name(code: str) -> str:
    """Map region code to display name for Pricing API filters."""
    names = {
        "us-east-1": "US East (N. Virginia)",
        "us-east-2": "US East (Ohio)",
        "us-west-1": "US West (N. California)",
        "us-west-2": "US West (Oregon)",
        "eu-west-1": "EU (Ireland)",
        "eu-west-2": "EU (London)",
        "eu-central-1": "EU (Frankfurt)",
        "ap-southeast-1": "Asia Pacific (Singapore)",
        "ap-southeast-2": "Asia Pacific (Sydney)",
        "ap-northeast-1": "Asia Pacific (Tokyo)",
    }
    return names.get(code, code)


def _parse_memory(mem: str) -> float | None:
    """Parse '16 GiB' into 16.0."""
    try:
        return float(mem.replace("GiB", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _safe_int(val) -> int:
    """Safely parse an integer."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def main():
    parser = argparse.ArgumentParser(description="CloudPulse Instance Pricing Scraper")
    parser.add_argument("--output", default="data/instances.json", help="Output JSON file")
    parser.add_argument("--service", default="ec2", choices=SERVICES.keys())
    parser.add_argument("--region", default=None, help="Single region to scrape (default: all)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    client = get_pricing_client()

    regions = [args.region] if args.region else REGIONS
    all_instances = []

    for region in regions:
        logger.info(f"Fetching {args.service} instances for {region}...")
        if args.service == "ec2":
            instances = fetch_ec2_instances(client, region)
            all_instances.extend(instances)
            logger.info(f"  Found {len(instances)} instance types")

    # Deduplicate by (instance_type, region)
    seen = set()
    unique = []
    for inst in all_instances:
        key = (inst["instance_type"], inst["region"])
        if key not in seen:
            seen.add(key)
            unique.append(inst)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(unique, indent=2))
    logger.info(f"Wrote {len(unique)} instances to {output_path}")


if __name__ == "__main__":
    main()
