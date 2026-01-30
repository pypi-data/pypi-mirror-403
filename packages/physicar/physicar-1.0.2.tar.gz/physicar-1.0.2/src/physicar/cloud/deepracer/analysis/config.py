"""
Analysis module configuration and MinIO client

Note: This module runs on the host, not inside Docker containers.
Therefore, it uses MINIO_HOST_URL (defaulting to 127.0.0.1:9000)
instead of DR_MINIO_URL (which is the Docker internal address).
"""
import os
import io
from pathlib import Path
from functools import lru_cache
from typing import Optional

# MinIO configuration (host-side access)
# Use MINIO_HOST_URL or default to localhost (NOT DR_MINIO_URL which is docker internal)
MINIO_ENDPOINT = os.environ.get("MINIO_HOST_URL", "http://127.0.0.1:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "physicar")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "physicar")
BUCKET = os.environ.get("DR_LOCAL_S3_BUCKET", "bucket")

# Track path (in simapp-mount)
ROUTES_PATH = Path(os.environ.get(
    "DR_ROUTES_PATH",
    os.path.expanduser("~/deepracer-simapp-mount/deepracer_simulation_environment/share/deepracer_simulation_environment/routes")
))


@lru_cache(maxsize=1)
def get_minio_client():
    """
    Get MinIO S3 client (cached)
    
    Returns:
        boto3.client: MinIO S3 client
    """
    import boto3
    from botocore.config import Config
    
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def list_models() -> list[str]:
    """
    List available models from MinIO
    
    Returns:
        list[str]: List of model names
    """
    s3 = get_minio_client()
    
    try:
        response = s3.list_objects_v2(
            Bucket=BUCKET,
            Prefix="models/",
            Delimiter="/"
        )
        
        models = []
        for prefix in response.get("CommonPrefixes", []):
            # "models/model_name/" -> "model_name"
            model_name = prefix["Prefix"].rstrip("/").split("/")[-1]
            if not model_name.startswith("."):
                models.append(model_name)
        
        return sorted(models)
    except Exception:
        return []


def list_s3_objects(prefix: str, delimiter: str = "") -> list[str]:
    """
    List objects in S3 bucket
    
    Args:
        prefix: S3 prefix
        delimiter: Delimiter for grouping
        
    Returns:
        list[str]: List of object keys
    """
    s3 = get_minio_client()
    
    try:
        kwargs = {"Bucket": BUCKET, "Prefix": prefix}
        if delimiter:
            kwargs["Delimiter"] = delimiter
            
        response = s3.list_objects_v2(**kwargs)
        
        if delimiter:
            # Return directory prefixes
            return [p["Prefix"] for p in response.get("CommonPrefixes", [])]
        else:
            # Return object keys
            return [obj["Key"] for obj in response.get("Contents", [])]
    except Exception:
        return []


def get_s3_object(key: str) -> Optional[bytes]:
    """
    Get object content from S3
    
    Args:
        key: S3 object key
        
    Returns:
        bytes: Object content or None if not found
    """
    s3 = get_minio_client()
    
    try:
        response = s3.get_object(Bucket=BUCKET, Key=key)
        return response["Body"].read()
    except Exception:
        return None


def get_s3_object_text(key: str, encoding: str = "utf-8") -> Optional[str]:
    """
    Get object content as text from S3
    
    Args:
        key: S3 object key
        encoding: Text encoding
        
    Returns:
        str: Object content as text or None if not found
    """
    content = get_s3_object(key)
    if content is not None:
        return content.decode(encoding)
    return None


def s3_object_exists(key: str) -> bool:
    """
    Check if object exists in S3
    
    Args:
        key: S3 object key
        
    Returns:
        bool: True if exists
    """
    s3 = get_minio_client()
    
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except Exception:
        return False


def get_model_prefix(model_name: str) -> str:
    """
    Get S3 prefix for model
    
    Args:
        model_name: Model name
        
    Returns:
        str: S3 prefix (e.g., "models/model_name/")
    """
    return f"models/{model_name}/"
