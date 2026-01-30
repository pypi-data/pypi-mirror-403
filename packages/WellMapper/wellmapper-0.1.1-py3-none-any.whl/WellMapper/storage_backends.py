"""Storage backends for plate layout exports with multi-format support"""
from pathlib import Path
from typing import Protocol, List, Dict, Any
import os
import io


class StorageBackend(Protocol):
    """Protocol for storage backends"""
    def write(self, filename: str, content: str) -> str:
        """Write content to storage, return the path/URL"""
        ...
    
    def write_dataframe(self, filename: str, data: List[Dict[str, Any]], format: str) -> str:
        """Write dataframe data to storage in specified format (csv/parquet/xlsx)"""
        ...
    
    def get_display_path(self, filename: str) -> str:
        """Get human-readable path for display"""
        ...


def _convert_to_format(data: List[Dict[str, Any]], format: str) -> bytes:
    """Convert list of dicts to specified format"""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas required for parquet and xlsx export.\n"
            "Install with: pip install pandas\n"
            "For parquet: pip install pandas pyarrow\n"
            "For xlsx: pip install pandas openpyxl"
        )
    
    df = pd.DataFrame(data)
    
    if format == "csv":
        return df.to_csv(index=False).encode('utf-8')
    
    elif format == "parquet":
        try:
            import pyarrow
        except ImportError:
            raise ImportError(
                "pyarrow required for parquet export.\n"
                "Install with: pip install pyarrow"
            )
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        return buffer.getvalue()
    
    elif format == "xlsx":
        try:
            import openpyxl
        except ImportError:
            raise ImportError(
                "openpyxl required for xlsx export.\n"
                "Install with: pip install openpyxl"
            )
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        return buffer.getvalue()
    
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'csv', 'parquet', or 'xlsx'")


class LocalStorage:
    """Local filesystem storage"""
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True, parents=True)
    
    def write(self, filename: str, content: str) -> str:
        path = self.base_path / filename
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(content)
        return str(path)
    
    def write_dataframe(self, filename: str, data: List[Dict[str, Any]], format: str) -> str:
        """Write dataframe to local storage"""
        # Change extension based on format
        base_name = Path(filename).stem
        parent = filename.rsplit("/", 1)[0] if "/" in filename else ""
        new_filename = f"{parent}/{base_name}.{format}" if parent else f"{base_name}.{format}"
        
        path = self.base_path / new_filename
        path.parent.mkdir(exist_ok=True, parents=True)
        
        content = _convert_to_format(data, format)
        path.write_bytes(content)
        return str(path)
    
    def get_display_path(self, filename: str) -> str:
        return str(self.base_path / filename)


class S3Storage:
    """AWS S3 storage backend"""
    def __init__(self, bucket: str, prefix: str = "", **kwargs):
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 required for S3 storage.\n"
                "Install with: pip install WellMapper[s3]\n"
                "Or: pip install boto3"
            )
        
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self.s3_client = boto3.client('s3', **kwargs)
    
    def write(self, filename: str, content: str) -> str:
        key = f"{self.prefix}/{filename}" if self.prefix else filename
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType='text/csv'
        )
        return f"s3://{self.bucket}/{key}"
    
    def write_dataframe(self, filename: str, data: List[Dict[str, Any]], format: str) -> str:
        """Write dataframe to S3"""
        # Change extension based on format
        base_name = Path(filename).stem
        parent = filename.rsplit("/", 1)[0] if "/" in filename else ""
        new_filename = f"{parent}/{base_name}.{format}" if parent else f"{base_name}.{format}"
        
        key = f"{self.prefix}/{new_filename}" if self.prefix else new_filename
        
        # Determine content type
        content_types = {
            'csv': 'text/csv',
            'parquet': 'application/octet-stream',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        content = _convert_to_format(data, format)
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=content_types.get(format, 'application/octet-stream')
        )
        return f"s3://{self.bucket}/{key}"
    
    def get_display_path(self, filename: str) -> str:
        key = f"{self.prefix}/{filename}" if self.prefix else filename
        return f"s3://{self.bucket}/{key}"


class AzureBlobStorage:
    """Azure Blob Storage backend"""
    def __init__(self, connection_string: str, container: str, prefix: str = ""):
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError:
            raise ImportError(
                "azure-storage-blob required for Azure storage.\n"
                "Install with: pip install WellMapper[azure]\n"
                "Or: pip install azure-storage-blob"
            )
        
        self.container = container
        self.prefix = prefix.rstrip("/")
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Ensure container exists
        try:
            self.blob_service_client.create_container(container)
        except Exception:
            pass  # Container already exists
    
    def write(self, filename: str, content: str) -> str:
        blob_name = f"{self.prefix}/{filename}" if self.prefix else filename
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container,
            blob=blob_name
        )
        blob_client.upload_blob(content.encode('utf-8'), overwrite=True)
        return f"azure://{self.container}/{blob_name}"
    
    def write_dataframe(self, filename: str, data: List[Dict[str, Any]], format: str) -> str:
        """Write dataframe to Azure Blob"""
        # Change extension based on format
        base_name = Path(filename).stem
        parent = filename.rsplit("/", 1)[0] if "/" in filename else ""
        new_filename = f"{parent}/{base_name}.{format}" if parent else f"{base_name}.{format}"
        
        blob_name = f"{self.prefix}/{new_filename}" if self.prefix else new_filename
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container,
            blob=blob_name
        )
        
        content = _convert_to_format(data, format)
        blob_client.upload_blob(content, overwrite=True)
        return f"azure://{self.container}/{blob_name}"
    
    def get_display_path(self, filename: str) -> str:
        blob_name = f"{self.prefix}/{filename}" if self.prefix else filename
        return f"azure://{self.container}/{blob_name}"


class GCSStorage:
    """Google Cloud Storage backend"""
    def __init__(self, bucket: str, prefix: str = "", project: str = None):
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError(
                "google-cloud-storage required for GCS.\n"
                "Install with: pip install WellMapper[gcs]\n"
                "Or: pip install google-cloud-storage"
            )
        
        self.bucket_name = bucket
        self.prefix = prefix.rstrip("/")
        client = storage.Client(project=project)
        self.bucket = client.bucket(bucket)
    
    def write(self, filename: str, content: str) -> str:
        blob_name = f"{self.prefix}/{filename}" if self.prefix else filename
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(content, content_type='text/csv')
        return f"gs://{self.bucket_name}/{blob_name}"
    
    def write_dataframe(self, filename: str, data: List[Dict[str, Any]], format: str) -> str:
        """Write dataframe to GCS"""
        # Change extension based on format
        base_name = Path(filename).stem
        parent = filename.rsplit("/", 1)[0] if "/" in filename else ""
        new_filename = f"{parent}/{base_name}.{format}" if parent else f"{base_name}.{format}"
        
        blob_name = f"{self.prefix}/{new_filename}" if self.prefix else new_filename
        blob = self.bucket.blob(blob_name)
        
        # Determine content type
        content_types = {
            'csv': 'text/csv',
            'parquet': 'application/octet-stream',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        content = _convert_to_format(data, format)
        blob.upload_from_string(content, content_type=content_types.get(format, 'application/octet-stream'))
        return f"gs://{self.bucket_name}/{blob_name}"
    
    def get_display_path(self, filename: str) -> str:
        blob_name = f"{self.prefix}/{filename}" if self.prefix else filename
        return f"gs://{self.bucket_name}/{blob_name}"


def create_storage_backend(storage_type: str = None, **kwargs) -> StorageBackend:
    """Factory function to create storage backend from environment or kwargs
    
    Reads configuration from .env file in current directory or environment variables.
    
    Args:
        storage_type: 'local', 's3', 'azure', or 'gcs'. If None, reads from STORAGE_TYPE env var
        **kwargs: Backend-specific configuration
    
    Environment Variables (from .env or system):
        STORAGE_TYPE: Backend type (local/s3/azure/gcs)
        
        For local:
            STORAGE_PATH: Base directory path
        
        For S3:
            S3_BUCKET: Bucket name
            S3_PREFIX: Optional prefix/folder
            AWS_ACCESS_KEY_ID: AWS credentials (or use IAM role)
            AWS_SECRET_ACCESS_KEY: AWS credentials
            AWS_REGION: AWS region
        
        For Azure:
            AZURE_STORAGE_CONNECTION_STRING: Connection string
            AZURE_CONTAINER: Container name
            AZURE_PREFIX: Optional prefix/folder
        
        For GCS:
            GCS_BUCKET: Bucket name
            GCS_PREFIX: Optional prefix/folder
            GCS_PROJECT: Optional project ID
            GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON
    """
    # Load from .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not required, just nice to have
    
    storage_type = storage_type or os.getenv("STORAGE_TYPE", "local")
    
    if storage_type == "local":
        path = kwargs.get("base_path") or os.getenv("STORAGE_PATH", "./data")
        return LocalStorage(base_path=path)
    
    elif storage_type == "s3":
        bucket = kwargs.get("bucket") or os.getenv("S3_BUCKET")
        if not bucket:
            raise ValueError("S3_BUCKET environment variable or 'bucket' kwarg required")
        
        prefix = kwargs.get("prefix") or os.getenv("S3_PREFIX", "")
        
        s3_kwargs = {}
        if os.getenv("AWS_REGION"):
            s3_kwargs["region_name"] = os.getenv("AWS_REGION")
        if os.getenv("AWS_ACCESS_KEY_ID"):
            s3_kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID")
        if os.getenv("AWS_SECRET_ACCESS_KEY"):
            s3_kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        s3_kwargs.update({k: v for k, v in kwargs.items() if k not in ['bucket', 'prefix']})
        
        return S3Storage(bucket=bucket, prefix=prefix, **s3_kwargs)
    
    elif storage_type == "azure":
        conn_str = kwargs.get("connection_string") or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not conn_str:
            raise ValueError(
                "AZURE_STORAGE_CONNECTION_STRING environment variable or "
                "'connection_string' kwarg required"
            )
        
        container = kwargs.get("container") or os.getenv("AZURE_CONTAINER", "data")
        prefix = kwargs.get("prefix") or os.getenv("AZURE_PREFIX", "")
        
        return AzureBlobStorage(
            connection_string=conn_str,
            container=container,
            prefix=prefix
        )
    
    elif storage_type == "gcs":
        bucket = kwargs.get("bucket") or os.getenv("GCS_BUCKET")
        if not bucket:
            raise ValueError("GCS_BUCKET environment variable or 'bucket' kwarg required")
        
        prefix = kwargs.get("prefix") or os.getenv("GCS_PREFIX", "")
        project = kwargs.get("project") or os.getenv("GCS_PROJECT")
        
        return GCSStorage(bucket=bucket, prefix=prefix, project=project)
    
    else:
        raise ValueError(
            f"Unknown storage type: {storage_type}. "
            "Supported: 'local', 's3', 'azure', 'gcs'"
        )