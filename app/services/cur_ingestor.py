"""
AWS Cost and Usage Report (CUR) Ingestor

Downloads CUR data from S3, normalizes it to FOCUS schema,
and writes Parquet files for DuckDB to query.

CUR data is typically delivered as gzipped CSV or Parquet in S3,
organized by billing period: s3://bucket/prefix/report/YYYYMM01-YYYYMM01/

Usage:
    ingestor = CURIngestor(role_arn="arn:aws:iam::123:role/CloudPulse")
    ingestor.ingest(year=2026, month=1)
"""

import csv
import gzip
import io
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.services.focus_schema import normalize_aws_cur, write_focus_parquet

logger = logging.getLogger(__name__)
settings = get_settings()


class CURIngestor:
    """Downloads and normalizes AWS CUR data from S3."""

    def __init__(
        self,
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        bucket: Optional[str] = None,
        prefix: Optional[str] = None,
        report_name: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        self.role_arn = role_arn
        self.external_id = external_id or settings.cloudpulse_external_id
        self.bucket = bucket or settings.cur_s3_bucket
        self.prefix = prefix or settings.cur_s3_prefix
        self.report_name = report_name or settings.cur_report_name
        self.output_dir = Path(output_dir or settings.billing_data_dir) / "aws"
        self._session: Optional[boto3.Session] = None

    def _get_session(self) -> boto3.Session:
        """Get a boto3 session, optionally assuming a cross-account role."""
        if self._session:
            return self._session

        if self.role_arn:
            sts = boto3.client("sts")
            kwargs = {
                "RoleArn": self.role_arn,
                "RoleSessionName": "cloudpulse-cur-reader",
                "DurationSeconds": 3600,
            }
            if self.external_id:
                kwargs["ExternalId"] = self.external_id

            try:
                resp = sts.assume_role(**kwargs)
                creds = resp["Credentials"]
                self._session = boto3.Session(
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"],
                )
            except ClientError as e:
                logger.error(f"Failed to assume role {self.role_arn}: {e}")
                raise
        else:
            # Use default credentials (local dev)
            self._session = boto3.Session()

        return self._session

    def _get_s3_client(self):
        return self._get_session().client("s3")

    def list_billing_periods(self) -> list[str]:
        """
        List available billing periods in the CUR S3 bucket.

        Returns list of period strings like '20260101-20260201'.
        """
        s3 = self._get_s3_client()
        prefix = f"{self.prefix}{self.report_name}/"

        try:
            resp = s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                Delimiter="/",
            )
        except ClientError as e:
            logger.error(f"Failed to list CUR periods: {e}")
            return []

        periods = []
        for cp in resp.get("CommonPrefixes", []):
            period = cp["Prefix"].rstrip("/").split("/")[-1]
            # Period format: YYYYMMDD-YYYYMMDD
            if len(period) == 17 and "-" in period:
                periods.append(period)

        periods.sort()
        logger.info(f"Found {len(periods)} billing periods in s3://{self.bucket}/{prefix}")
        return periods

    def _list_cur_files(self, period: str) -> list[str]:
        """List all CUR data files for a billing period."""
        s3 = self._get_s3_client()
        prefix = f"{self.prefix}{self.report_name}/{period}/"

        try:
            paginator = s3.get_paginator("list_objects_v2")
            keys = []
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    # CUR files are .csv.gz or .parquet
                    if key.endswith(".csv.gz") or key.endswith(".parquet"):
                        keys.append(key)
            return keys
        except ClientError as e:
            logger.error(f"Failed to list CUR files for {period}: {e}")
            return []

    def _read_csv_gz(self, key: str) -> list[dict]:
        """Download and parse a gzipped CSV CUR file from S3."""
        s3 = self._get_s3_client()
        try:
            resp = s3.get_object(Bucket=self.bucket, Key=key)
            compressed = resp["Body"].read()
            decompressed = gzip.decompress(compressed)
            text = decompressed.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            logger.info(f"Read {len(rows)} rows from s3://{self.bucket}/{key}")
            return rows
        except ClientError as e:
            logger.error(f"Failed to read {key}: {e}")
            return []

    def _read_parquet_s3(self, key: str) -> list[dict]:
        """Download and read a Parquet CUR file from S3."""
        import pyarrow.parquet as pq

        s3 = self._get_s3_client()
        try:
            resp = s3.get_object(Bucket=self.bucket, Key=key)
            data = resp["Body"].read()

            buf = io.BytesIO(data)
            table = pq.read_table(buf)
            rows = table.to_pydict()

            # Convert columnar dict to list of row dicts
            num_rows = len(next(iter(rows.values())))
            result = []
            for i in range(num_rows):
                result.append({col: rows[col][i] for col in rows})

            logger.info(f"Read {len(result)} rows from s3://{self.bucket}/{key}")
            return result
        except ClientError as e:
            logger.error(f"Failed to read parquet {key}: {e}")
            return []

    def ingest_period(self, period: str) -> int:
        """
        Ingest a single billing period.

        Downloads CUR files, normalizes to FOCUS, writes Parquet.
        Returns number of rows ingested.
        """
        keys = self._list_cur_files(period)
        if not keys:
            logger.warning(f"No CUR files found for period {period}")
            return 0

        all_rows = []
        for key in keys:
            if key.endswith(".csv.gz"):
                all_rows.extend(self._read_csv_gz(key))
            elif key.endswith(".parquet"):
                all_rows.extend(self._read_parquet_s3(key))

        if not all_rows:
            return 0

        # Normalize to FOCUS schema
        normalized = normalize_aws_cur(all_rows)

        if not normalized:
            return 0

        # Write to Parquet
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(self.output_dir / f"cur_{period}.parquet")
        write_focus_parquet(normalized, output_path)

        return len(normalized)

    def ingest(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> dict:
        """
        Ingest CUR data. If year/month specified, ingests that period only.
        Otherwise, ingests all available periods.

        Returns: {"periods_processed": N, "total_rows": N}
        """
        periods = self.list_billing_periods()

        if year and month:
            target = f"{year}{month:02d}01"
            periods = [p for p in periods if p.startswith(target)]

        total_rows = 0
        processed = 0

        for period in periods:
            rows = self.ingest_period(period)
            if rows > 0:
                total_rows += rows
                processed += 1
                logger.info(f"Ingested {rows} rows for period {period}")

        result = {
            "periods_processed": processed,
            "total_rows": total_rows,
            "output_dir": str(self.output_dir),
        }
        logger.info(f"CUR ingestion complete: {result}")
        return result

    def ingest_from_local_csv(self, csv_path: str) -> int:
        """
        Ingest CUR data from a local CSV file (for development/testing).

        Args:
            csv_path: Path to a local CUR CSV file.

        Returns:
            Number of rows ingested.
        """
        path = Path(csv_path)
        if not path.exists():
            logger.error(f"File not found: {csv_path}")
            return 0

        if path.suffix == ".gz":
            with gzip.open(path, "rt") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        else:
            with open(path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

        logger.info(f"Read {len(rows)} rows from {csv_path}")

        normalized = normalize_aws_cur(rows)
        if not normalized:
            return 0

        self.output_dir.mkdir(parents=True, exist_ok=True)
        stem = path.stem.replace(".csv", "")
        output_path = str(self.output_dir / f"cur_{stem}.parquet")
        write_focus_parquet(normalized, output_path)

        return len(normalized)
