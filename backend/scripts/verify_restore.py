#!/usr/bin/env python3
"""
Downloads the latest backup from R2 and restores it to a test PostgreSQL instance.
Exits non-zero if the backup is corrupt or restore fails.

Required env vars:
    DATABASE_URL          postgresql://... pointing at the TEST database to restore into
    R2_ENDPOINT
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_BUCKET
"""
import logging
import os
import subprocess
import sys
from urllib.parse import urlparse

import boto3
from botocore.client import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TABLES_TO_CHECK = ("users", "transactions", "categories", "goals", "budgets")


def _parse_db_url(url: str) -> dict:
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    p = urlparse(url)
    return {
        "host": p.hostname or "localhost",
        "port": str(p.port or 5432),
        "user": p.username or "postgres",
        "password": p.password or "",
        "dbname": p.path.lstrip("/").split("?")[0],
    }


def _latest_key(s3, bucket: str) -> str:
    resp = s3.list_objects_v2(Bucket=bucket, Prefix="backups/")
    objects = resp.get("Contents", [])
    if not objects:
        logger.error("No backups found in R2 bucket '%s'", bucket)
        sys.exit(1)
    return max(objects, key=lambda o: o["LastModified"])["Key"]


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    r2_endpoint = os.environ["R2_ENDPOINT"]
    r2_access_key = os.environ["R2_ACCESS_KEY_ID"]
    r2_secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
    r2_bucket = os.environ["R2_BUCKET"]

    db = _parse_db_url(database_url)
    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]

    s3 = boto3.client(
        "s3",
        endpoint_url=r2_endpoint,
        aws_access_key_id=r2_access_key,
        aws_secret_access_key=r2_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

    key = _latest_key(s3, r2_bucket)
    local_path = "/tmp/restore_verify.dump"
    logger.info("Downloading backup: %s", key)
    s3.download_file(r2_bucket, key, local_path)

    # Structural integrity check — no DB connection needed
    logger.info("Verifying backup integrity (pg_restore --list)")
    result = subprocess.run(  # nosec B603 B607
        ["pg_restore", "--list", local_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Backup is corrupt:\n%s", result.stderr)
        sys.exit(1)
    table_count = result.stdout.count("TABLE DATA")
    logger.info("Backup integrity OK — %d TABLE DATA sections", table_count)

    # Full restore to the test database
    logger.info("Restoring to %s@%s:%s/%s", db["user"], db["host"], db["port"], db["dbname"])
    result = subprocess.run(  # nosec B603 B607
        [
            "pg_restore",
            "-h", db["host"],
            "-p", db["port"],
            "-U", db["user"],
            "-d", db["dbname"],
            "--no-owner",
            "--no-privileges",
            "--clean",
            "--if-exists",
            local_path,
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    # pg_restore exits 1 for non-fatal warnings (e.g. object didn't exist on --clean)
    if result.returncode > 1:
        logger.error("pg_restore failed:\n%s", result.stderr)
        sys.exit(1)
    if result.stderr:
        logger.warning("pg_restore warnings (non-fatal):\n%s", result.stderr)

    # Sanity-check: each expected table is queryable
    for table in TABLES_TO_CHECK:
        result = subprocess.run(  # nosec B603 B607
            [
                "psql",
                "-h", db["host"],
                "-p", db["port"],
                "-U", db["user"],
                "-d", db["dbname"],
                "-t",
                "-c", f"SELECT COUNT(*) FROM {table};",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error("Table '%s' not queryable: %s", table, result.stderr)
            sys.exit(1)
        logger.info("Table '%s': %s rows", table, result.stdout.strip())

    os.unlink(local_path)
    logger.info("Restore verification passed")


if __name__ == "__main__":
    main()
