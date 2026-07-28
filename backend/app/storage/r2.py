from functools import lru_cache
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings


def _get_client():
    """Returns a boto3 S3 client pointed at Cloudflare R2."""
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


def upload_file(
    file_obj: BinaryIO,
    key: str,
    content_type: str,
) -> str:
    """
    Uploads a file-like object to R2.

    Args:
        file_obj:     Readable binary stream (e.g. SpooledTemporaryFile from FastAPI).
        key:          The R2 object key (e.g. "videos/user-id/video-id.mp4").
        content_type: MIME type of the file.

    Returns:
        The object key on success.

    Raises:
        ClientError: If the upload fails.
    """
    settings = get_settings()
    client = _get_client()
    client.upload_fileobj(
        file_obj,
        settings.r2_bucket_name,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """
    Generates a time-limited presigned URL for a private R2 object.

    Args:
        key:        The R2 object key.
        expires_in: Seconds until the URL expires (default: 1 hour).

    Returns:
        A presigned HTTPS URL string.
    """
    settings = get_settings()
    client = _get_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": key},
        ExpiresIn=expires_in,
    )
    return url


def delete_file(key: str) -> None:
    """
    Deletes an object from R2. Silently ignores 'key not found' errors.

    Args:
        key: The R2 object key to delete.
    """
    settings = get_settings()
    client = _get_client()
    try:
        client.delete_object(Bucket=settings.r2_bucket_name, Key=key)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code != "NoSuchKey":
            raise
