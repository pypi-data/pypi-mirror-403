"""Common S3 based resources for any data pipeline."""

from typing import Self

from dagster import ConfigurableResource
from s3path import S3Path


class S3Bucket(ConfigurableResource):
    """Configuration for the data ingest bucket."""

    s3_bucket: str
    s3_prefix: str = ""

    def path(self: Self) -> S3Path:
        """Return the S3Path for the configured bucket and prefix."""
        return S3Path(f"/{self.s3_bucket}/{self.s3_prefix}")
