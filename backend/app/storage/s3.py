"""
storage/s3.py  ── S3 Storage helpers

Assumes:
  - STORAGE_BUCKET env var for the S3/MinIO bucket name
  - AWS_* / MINIO_* env vars handled by boto3 automatically
    (or passed via config.py Settings)
"""

import json
import logging
import os
import tempfile
from functools import lru_cache
from typing import Any, Optional
import pandas as pd

import aioboto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _session() -> aioboto3.Session:
    return aioboto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def _client_kwargs() -> dict:
    kwargs: dict = {}
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    return kwargs


class S3Storage:
    def __init__(self, bucket: Optional[str] = None):
        self.bucket = bucket or settings.STORAGE_BUCKET

    async def _client(self):
        return await _session().client("s3", **_client_kwargs())

    async def upload_bytes(self, data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
        async with await self._client() as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        logger.debug("Uploaded to s3://%s/%s", self.bucket, key)
        return key

    async def download_bytes(self, key: str) -> bytes:
        async with await self._client() as s3:
            resp = await s3.get_object(Bucket=self.bucket, Key=key)
            return await resp["Body"].read()

    async def download_to_tmp(self, key: str) -> str:
        data = await self.download_bytes(key)
        suffix = os.path.splitext(key)[1] or ".tmp"
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.write(fd, data)
        os.close(fd)
        return path

    async def delete(self, key: str) -> None:
        async with await self._client() as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)
        logger.debug("Deleted s3://%s/%s", self.bucket, key)

    async def presigned_url(self, key: str, expires_in: int = 3600) -> str:
        async with await self._client() as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )

    async def upload_json(self, key: str, payload: Any) -> str:
        body = json.dumps(payload, default=str).encode()
        return await self.upload_bytes(body, key, "application/json")

    async def download_json(self, key: str) -> Any:
        data = await self.download_bytes(key)
        return json.loads(data)


async def upload_json(key: str, payload: Any, *, bucket: str | None = None) -> str:
    s3 = S3Storage(bucket)
    return await s3.upload_json(key, payload)


async def download_json(key: str, *, bucket: str | None = None) -> Any:
    s3 = S3Storage(bucket)
    return await s3.download_json(key)


async def download_parquet(key: str, *, bucket: str | None = None) -> pd.DataFrame:
    import pandas as pd
    s3 = S3Storage(bucket)
    data = await s3.download_bytes(key)
    from io import BytesIO
    return pd.read_parquet(BytesIO(data))


async def delete_object(key: str, *, bucket: str | None = None) -> None:
    s3 = S3Storage(bucket)
    await s3.delete(key)


async def generate_presigned_url(
    key: str,
    *,
    bucket: str | None = None,
    expires_in: int = 3600,
) -> str:
    s3 = S3Storage(bucket)
    return await s3.presigned_url(key, expires_in)