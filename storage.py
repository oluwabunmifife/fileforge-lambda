import logging
from pathlib import Path

import boto3

LOGGER = logging.getLogger(__name__)
S3_CLIENT = boto3.client("s3")


def download_file(bucket: str, key: str, local_path: str) -> None:
    """Download an object from S3 to a local file path."""
    destination = Path(local_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Downloading s3://%s/%s to %s", bucket, key, destination)
    S3_CLIENT.download_file(bucket, key, str(destination))



def upload_file(bucket: str, key: str, local_path: str) -> None:
    """Upload a local file to S3."""
    source = Path(local_path)
    LOGGER.info("Uploading %s to s3://%s/%s", source, bucket, key)
    extra_args = {"ContentType": "image/jpeg"} if source.suffix.lower() == ".jpg" else None
    if extra_args:
        S3_CLIENT.upload_file(str(source), bucket, key, ExtraArgs=extra_args)
        return

    S3_CLIENT.upload_file(str(source), bucket, key)
