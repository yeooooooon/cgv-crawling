"""S3 storage helpers for pipeline outputs."""

from io import BytesIO
import os
from pathlib import Path

import pandas as pd


def get_bucket_name() -> str | None:
    """Return the configured output bucket, or None for local runs."""

    return os.getenv('DATA_BUCKET')


def upload_dataframe(dataframe: pd.DataFrame, key: str) -> str | None:
    """Upload a dataframe as UTF-8 CSV when an S3 bucket is configured."""

    bucket_name = get_bucket_name()
    if not bucket_name:
        return None

    import boto3

    buffer = BytesIO()
    dataframe.to_csv(buffer, index=False, encoding='utf-8-sig')
    boto3.client('s3').put_object(
        Bucket=bucket_name,
        Key=key,
        Body=buffer.getvalue(),
        ContentType='text/csv; charset=utf-8',
    )
    return f's3://{bucket_name}/{key}'


def upload_directory(directory: Path, prefix: str) -> list[str]:
    """Upload all files below a directory under an S3 prefix."""

    bucket_name = get_bucket_name()
    if not bucket_name or not directory.exists():
        return []

    import boto3

    client = boto3.client('s3')
    uploaded_keys = []
    for file_path in directory.rglob('*'):
        if not file_path.is_file():
            continue

        key = f"{prefix.rstrip('/')}/{file_path.relative_to(directory).as_posix()}"
        client.upload_file(str(file_path), bucket_name, key)
        uploaded_keys.append(key)

    return uploaded_keys