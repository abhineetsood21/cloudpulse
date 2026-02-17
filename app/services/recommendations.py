"""
Recommendation Engine

Scans customer AWS accounts for waste:
- Idle EC2 instances (low CPU)
- Unused EBS volumes (not attached)
- Old EBS snapshots (>90 days)
"""

import logging
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.models.models import ResourceType

logger = logging.getLogger(__name__)
settings = get_settings()

# Rough monthly cost estimates per instance type (on-demand, us-east-1, USD)
# This is a simplified lookup — in production, use the AWS Pricing API
EC2_HOURLY_COSTS = {
    "t2.micro": 0.0116,
    "t2.small": 0.023,
    "t2.medium": 0.0464,
    "t2.large": 0.0928,
    "t3.micro": 0.0104,
    "t3.small": 0.0208,
    "t3.medium": 0.0416,
    "t3.large": 0.0832,
    "m5.large": 0.096,
    "m5.xlarge": 0.192,
    "m5.2xlarge": 0.384,
    "c5.large": 0.085,
    "c5.xlarge": 0.17,
    "r5.large": 0.126,
    "r5.xlarge": 0.252,
}

# EBS cost per GB/month (gp2/gp3 approximate)
EBS_GB_MONTHLY_COST = 0.08

# Snapshot cost per GB/month
SNAPSHOT_GB_MONTHLY_COST = 0.05


class RecommendationEngine:
    """Scans AWS accounts for cost optimization opportunities."""

    def __init__(self, session: boto3.Session):
        self.session = session

    def _get_ec2_client(self, region: str):
        return self.session.client("ec2", region_name=region)

    def _get_cloudwatch_client(self, region: str):
        return self.session.client("cloudwatch", region_name=region)

    def get_active_regions(self) -> list[str]:
        """Get list of AWS regions that have EC2 resources."""
        ec2 = self._get_ec2_client("us-east-1")
        try:
            response = ec2.describe_regions(
                Filters=[{"Name": "opt-in-status", "Values": ["opt-in-not-required", "opted-in"]}]
            )
            return [r["RegionName"] for r in response["Regions"]]
        except ClientError as e:
            logger.error(f"Failed to list regions: {e}")
            return ["us-east-1"]

    def find_idle_ec2_instances(
        self,
        region: str,
        cpu_threshold: float = 5.0,
        lookback_days: int = 7,
    ) -> list[dict]:
        """
        Find EC2 instances with average CPU utilization below threshold.

        Returns list of recommendations.
        """
        ec2 = self._get_ec2_client(region)
        cw = self._get_cloudwatch_client(region)

        try:
            response = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )
        except ClientError as e:
            logger.error(f"Failed to describe instances in {region}: {e}")
            return []

        recommendations = []
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=lookback_days)

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_id = instance["InstanceId"]
                instance_type = instance.get("InstanceType", "unknown")

                # Get average CPU utilization
                try:
                    metrics = cw.get_metric_statistics(
                        Namespace="AWS/EC2",
                        MetricName="CPUUtilization",
                        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # 1 day
                        Statistics=["Average"],
                    )
                except ClientError as e:
                    logger.warning(f"Failed to get CPU metrics for {instance_id}: {e}")
                    continue

                datapoints = metrics.get("Datapoints", [])
                if not datapoints:
                    continue

                avg_cpu = sum(dp["Average"] for dp in datapoints) / len(datapoints)

                if avg_cpu < cpu_threshold:
                    hourly_cost = EC2_HOURLY_COSTS.get(instance_type, 0.05)
                    monthly_cost = hourly_cost * 730  # ~730 hours/month

                    # Get instance name tag
                    name = "Unnamed"
                    for tag in instance.get("Tags", []):
                        if tag["Key"] == "Name":
                            name = tag["Value"]
                            break

                    recommendations.append({
                        "resource_type": ResourceType.EC2_INSTANCE.value,
                        "resource_id": instance_id,
                        "region": region,
                        "recommendation": (
                            f"Instance '{name}' ({instance_type}) has avg CPU "
                            f"of {avg_cpu:.1f}% over {lookback_days} days. "
                            f"Consider stopping, rightsizing, or converting to spot."
                        ),
                        "estimated_monthly_savings": round(monthly_cost, 2),
                        "details": {
                            "instance_type": instance_type,
                            "avg_cpu": round(avg_cpu, 2),
                            "name": name,
                        },
                    })

        return recommendations

    def find_unused_ebs_volumes(self, region: str) -> list[dict]:
        """Find EBS volumes that are not attached to any instance."""
        ec2 = self._get_ec2_client(region)

        try:
            response = ec2.describe_volumes(
                Filters=[{"Name": "status", "Values": ["available"]}]
            )
        except ClientError as e:
            logger.error(f"Failed to describe volumes in {region}: {e}")
            return []

        recommendations = []

        for volume in response.get("Volumes", []):
            volume_id = volume["VolumeId"]
            size_gb = volume.get("Size", 0)
            monthly_cost = size_gb * EBS_GB_MONTHLY_COST

            # Get name tag
            name = "Unnamed"
            for tag in volume.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
                    break

            recommendations.append({
                "resource_type": ResourceType.EBS_VOLUME.value,
                "resource_id": volume_id,
                "region": region,
                "recommendation": (
                    f"EBS volume '{name}' ({size_gb} GB, {volume.get('VolumeType', 'unknown')}) "
                    f"is not attached to any instance. Consider deleting or snapshotting."
                ),
                "estimated_monthly_savings": round(monthly_cost, 2),
                "details": {
                    "size_gb": size_gb,
                    "volume_type": volume.get("VolumeType"),
                    "name": name,
                },
            })

        return recommendations

    def find_old_snapshots(
        self,
        region: str,
        max_age_days: int = 90,
    ) -> list[dict]:
        """Find EBS snapshots older than max_age_days."""
        ec2 = self._get_ec2_client(region)

        try:
            response = ec2.describe_snapshots(OwnerIds=["self"])
        except ClientError as e:
            logger.error(f"Failed to describe snapshots in {region}: {e}")
            return []

        recommendations = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        for snapshot in response.get("Snapshots", []):
            start_time = snapshot.get("StartTime")
            if not start_time or start_time > cutoff_date:
                continue

            snapshot_id = snapshot["SnapshotId"]
            size_gb = snapshot.get("VolumeSize", 0)
            monthly_cost = size_gb * SNAPSHOT_GB_MONTHLY_COST
            age_days = (datetime.now(timezone.utc) - start_time).days

            description = snapshot.get("Description", "No description")

            recommendations.append({
                "resource_type": ResourceType.EBS_SNAPSHOT.value,
                "resource_id": snapshot_id,
                "region": region,
                "recommendation": (
                    f"Snapshot ({size_gb} GB) is {age_days} days old. "
                    f"Description: '{description[:100]}'. "
                    f"Consider deleting if no longer needed."
                ),
                "estimated_monthly_savings": round(monthly_cost, 2),
                "details": {
                    "size_gb": size_gb,
                    "age_days": age_days,
                    "description": description,
                },
            })

        return recommendations

    def find_idle_rds_instances(self, region: str) -> list[dict]:
        """Find RDS instances with low average connections over 7 days."""
        rds = self.session.client("rds", region_name=region)
        cw = self._get_cloudwatch_client(region)

        try:
            response = rds.describe_db_instances()
        except ClientError as e:
            logger.error(f"Failed to describe RDS instances in {region}: {e}")
            return []

        recommendations = []
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=7)

        for db in response.get("DBInstances", []):
            if db.get("DBInstanceStatus") != "available":
                continue

            db_id = db["DBInstanceIdentifier"]
            db_class = db.get("DBInstanceClass", "unknown")

            try:
                metrics = cw.get_metric_statistics(
                    Namespace="AWS/RDS",
                    MetricName="DatabaseConnections",
                    Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,
                    Statistics=["Average"],
                )
            except ClientError:
                continue

            datapoints = metrics.get("Datapoints", [])
            if not datapoints:
                continue

            avg_connections = sum(dp["Average"] for dp in datapoints) / len(datapoints)

            if avg_connections < 1:
                # Rough monthly cost estimate
                monthly_cost = 50.00  # placeholder — use Pricing API in production
                recommendations.append({
                    "resource_type": ResourceType.RDS_INSTANCE.value,
                    "resource_id": db_id,
                    "region": region,
                    "recommendation": (
                        f"RDS instance '{db_id}' ({db_class}) has avg {avg_connections:.1f} "
                        f"connections over 7 days. Consider stopping or deleting."
                    ),
                    "estimated_monthly_savings": round(monthly_cost, 2),
                    "details": {
                        "db_class": db_class,
                        "engine": db.get("Engine"),
                        "avg_connections": round(avg_connections, 2),
                    },
                })

        return recommendations

    def find_unused_elastic_ips(self, region: str) -> list[dict]:
        """Find Elastic IPs that are not associated with any instance."""
        ec2 = self._get_ec2_client(region)

        try:
            response = ec2.describe_addresses()
        except ClientError as e:
            logger.error(f"Failed to describe addresses in {region}: {e}")
            return []

        recommendations = []
        for addr in response.get("Addresses", []):
            if not addr.get("AssociationId"):
                recommendations.append({
                    "resource_type": ResourceType.ELASTIC_IP.value,
                    "resource_id": addr.get("AllocationId", ""),
                    "region": region,
                    "recommendation": (
                        f"Elastic IP {addr.get('PublicIp')} is not associated. "
                        f"Unattached EIPs cost $3.60/month."
                    ),
                    "estimated_monthly_savings": 3.60,
                    "details": {"public_ip": addr.get("PublicIp")},
                })

        return recommendations

    def find_idle_load_balancers(self, region: str) -> list[dict]:
        """Find ALBs/NLBs with zero healthy targets."""
        elbv2 = self.session.client("elbv2", region_name=region)

        try:
            lbs = elbv2.describe_load_balancers().get("LoadBalancers", [])
        except ClientError as e:
            logger.error(f"Failed to describe load balancers in {region}: {e}")
            return []

        recommendations = []
        for lb in lbs:
            lb_arn = lb["LoadBalancerArn"]
            lb_name = lb.get("LoadBalancerName", "")

            try:
                tgs = elbv2.describe_target_groups(LoadBalancerArn=lb_arn)
                has_targets = False
                for tg in tgs.get("TargetGroups", []):
                    health = elbv2.describe_target_health(
                        TargetGroupArn=tg["TargetGroupArn"]
                    )
                    if health.get("TargetHealthDescriptions"):
                        has_targets = True
                        break

                if not has_targets:
                    monthly_cost = 16.20 if lb.get("Type") == "application" else 22.50
                    recommendations.append({
                        "resource_type": ResourceType.LOAD_BALANCER.value,
                        "resource_id": lb_name,
                        "region": region,
                        "recommendation": (
                            f"{lb.get('Type', 'application').upper()} load balancer '{lb_name}' "
                            f"has no healthy targets. Consider deleting."
                        ),
                        "estimated_monthly_savings": round(monthly_cost, 2),
                        "details": {"type": lb.get("Type"), "dns": lb.get("DNSName")},
                    })
            except ClientError:
                continue

        return recommendations

    def scan_all(self, regions: list[str] | None = None) -> list[dict]:
        """
        Run all recommendation scans across specified regions.

        Returns combined list of all recommendations.
        """
        if not regions:
            regions = ["us-east-1", "us-west-2", "eu-west-1"]  # Common defaults

        all_recommendations = []

        for region in regions:
            logger.info(f"Scanning {region} for recommendations...")

            all_recommendations.extend(self.find_idle_ec2_instances(region))
            all_recommendations.extend(self.find_unused_ebs_volumes(region))
            all_recommendations.extend(self.find_old_snapshots(region))
            all_recommendations.extend(self.find_idle_rds_instances(region))
            all_recommendations.extend(self.find_unused_elastic_ips(region))
            all_recommendations.extend(self.find_idle_load_balancers(region))

        # Sort by estimated savings (highest first)
        all_recommendations.sort(
            key=lambda r: r["estimated_monthly_savings"], reverse=True
        )

        total_savings = sum(r["estimated_monthly_savings"] for r in all_recommendations)
        logger.info(
            f"Found {len(all_recommendations)} recommendations, "
            f"estimated total savings: ${total_savings:.2f}/month"
        )

        return all_recommendations
