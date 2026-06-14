#!/usr/bin/env python3
"""
Dumps the PostgreSQL database and uploads the backup to Cloudflare R2.

Required env vars:
    DATABASE_URL        postgresql+asyncpg://... or postgresql://...
    R2_ENDPOINT         https://<account-id>.r2.cloudflarestorage.com
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_BUCKET
"""
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

import boto3
from botocore.client import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _parse_db_url(url: str) -> dict:
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    p = urlparse(url)
    return {
        "host": p.hostname,
        "port": str(p.port or 5432),
        "user": p.username,
        "password": p.password or "",
        "dbname": p.path.lstrip("/").split("?")[0],
    }


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    r2_endpoint = os.environ["R2_ENDPOINT"]
    r2_access_key = os.environ["R2_ACCESS_KEY_ID"]
    r2_secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
    r2_bucket = os.environ["R2_BUCKET"]

    db = _parse_db_url(database_url)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dump_path = f"/tmp/budget_{timestamp}.dump"
    object_key = f"backups/{timestamp}/budget_{timestamp}.dump"

    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]

    logger.info("pg_dump → %s (host=%s db=%s)", dump_path, db["host"], db["dbname"])
    result = subprocess.run(  # nosec B603 B607
        [
            "pg_dump",
            "-h", db["host"],
            "-p", db["port"],
            "-U", db["user"],
            "-d", db["dbname"],
            "-F", "c",
            "-f", dump_path,
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("pg_dump failed:\n%s", result.stderr)
        sys.exit(1)

    logger.info("Uploading to R2: %s/%s", r2_bucket, object_key)
    s3 = boto3.client(
        "s3",
        endpoint_url=r2_endpoint,
        aws_access_key_id=r2_access_key,
        aws_secret_access_key=r2_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )
    s3.upload_file(dump_path, r2_bucket, object_key)
    os.unlink(dump_path)

    logger.info("Backup complete: %s", object_key)


if __name__ == "__main__":
    main()
