"""Storage provider abstraction for batch file management.

This module provides a common interface for different storage backends:
- Azure Blob Storage
- AWS S3
- Google Cloud Storage
- Local filesystem
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class StorageProvider(ABC):
    """Abstract base class for storage providers."""

    @abstractmethod
    async def upload_file(self, data: bytes, path: str, content_type: Optional[str] = None) -> str:
        """Upload file to storage.

        Args:
            data: File data as bytes
            path: Destination path
            content_type: Optional content type

        Returns:
            URL or path to uploaded file
        """
        pass

    @abstractmethod
    async def upload_stream(
        self, stream: io.BytesIO, path: str, content_type: Optional[str] = None
    ) -> str:
        """Upload from stream to storage.

        Args:
            stream: BytesIO stream
            path: Destination path
            content_type: Optional content type

        Returns:
            URL or path to uploaded file
        """
        pass

    @abstractmethod
    async def download_file(self, path: str) -> Optional[bytes]:
        """Download file from storage.

        Args:
            path: Source path

        Returns:
            File data as bytes, or None if not found
        """
        pass

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """Delete file from storage.

        Args:
            path: Path to delete

        Returns:
            True if deleted, False otherwise
        """
        pass

    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: Path to check

        Returns:
            True if exists, False otherwise
        """
        pass


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider."""

    def __init__(self, base_dir: str = "./storage"):
        """Initialize local storage.

        Args:
            base_dir: Base directory for storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, data: bytes, path: str, content_type: Optional[str] = None) -> str:
        """Upload file to local storage."""
        file_path = self.base_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(data)

        return str(file_path)

    async def upload_stream(
        self, stream: io.BytesIO, path: str, content_type: Optional[str] = None
    ) -> str:
        """Upload from stream to local storage."""
        data = stream.getvalue()
        return await self.upload_file(data, path, content_type)

    async def download_file(self, path: str) -> Optional[bytes]:
        """Download file from local storage."""
        file_path = self.base_dir / path

        if not file_path.exists():
            return None

        with open(file_path, "rb") as f:
            return f.read()

    async def delete_file(self, path: str) -> bool:
        """Delete file from local storage."""
        file_path = self.base_dir / path

        if not file_path.exists():
            return False

        file_path.unlink()
        return True

    async def file_exists(self, path: str) -> bool:
        """Check if file exists in local storage."""
        file_path = self.base_dir / path
        return file_path.exists()


class AzureBlobStorageProvider(StorageProvider):
    """Azure Blob Storage provider.

    Requires srx-lib-azure package.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        account_key: Optional[str] = None,
        base_blob_url: Optional[str] = None,
        sas_token: Optional[str] = None,
    ):
        """Initialize Azure Blob Storage.

        Args:
            connection_string: Azure Storage connection string
            account_key: Azure Storage account key
            base_blob_url: Base blob URL
            sas_token: SAS token
        """
        try:
            from srx_lib_azure import AzureBlobService
        except ImportError as exc:
            raise ImportError(
                "srx-lib-azure required for Azure Blob Storage support. "
                "Install with: pip install srx-lib-azure"
            ) from exc

        self.service = AzureBlobService(
            connection_string=connection_string,
            account_key=account_key,
            base_blob_url=base_blob_url,
            sas_token=sas_token,
            warn_if_unconfigured=False,
        )

    async def upload_file(self, data: bytes, path: str, content_type: Optional[str] = None) -> str:
        """Upload file to Azure Blob Storage."""
        stream = io.BytesIO(data)
        return await self.upload_stream(stream, path, content_type)

    async def upload_stream(
        self, stream: io.BytesIO, path: str, content_type: Optional[str] = None
    ) -> str:
        """Upload from stream to Azure Blob Storage."""
        await self.service.upload_stream(stream, path, content_type=content_type)
        return path

    async def download_file(self, path: str) -> Optional[bytes]:
        """Download file from Azure Blob Storage."""
        return await self.service.download_file(path)

    async def delete_file(self, path: str) -> bool:
        """Delete file from Azure Blob Storage."""
        try:
            await self.service.delete_file(path)
            return True
        except Exception:
            return False

    async def file_exists(self, path: str) -> bool:
        """Check if file exists in Azure Blob Storage."""
        data = await self.download_file(path)
        return data is not None


class S3StorageProvider(StorageProvider):
    """AWS S3 storage provider.

    Requires boto3 package.
    """

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None,
    ):
        """Initialize S3 storage.

        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
            region_name: AWS region
        """
        try:
            import boto3
        except ImportError as exc:
            raise ImportError(
                "boto3 required for S3 support. Install with: pip install boto3"
            ) from exc

        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    async def upload_file(self, data: bytes, path: str, content_type: Optional[str] = None) -> str:
        """Upload file to S3."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.s3_client.put_object(Bucket=self.bucket_name, Key=path, Body=data, **extra_args)

        return f"s3://{self.bucket_name}/{path}"

    async def upload_stream(
        self, stream: io.BytesIO, path: str, content_type: Optional[str] = None
    ) -> str:
        """Upload from stream to S3."""
        data = stream.getvalue()
        return await self.upload_file(data, path, content_type)

    async def download_file(self, path: str) -> Optional[bytes]:
        """Download file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=path)
            return response["Body"].read()
        except Exception:
            return None

    async def delete_file(self, path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=path)
            return True
        except Exception:
            return False

    async def file_exists(self, path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=path)
            return True
        except Exception:
            return False


class GCSStorageProvider(StorageProvider):
    """Google Cloud Storage provider.

    Requires google-cloud-storage package.
    """

    def __init__(
        self,
        bucket_name: str,
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ):
        """Initialize GCS storage.

        Args:
            bucket_name: GCS bucket name
            project_id: GCP project ID
            credentials_path: Path to credentials JSON file
        """
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise ImportError(
                "google-cloud-storage required for GCS support. "
                "Install with: pip install google-cloud-storage"
            ) from exc

        if credentials_path:
            self.client = storage.Client.from_service_account_json(
                credentials_path, project=project_id
            )
        else:
            self.client = storage.Client(project=project_id)

        self.bucket = self.client.bucket(bucket_name)

    async def upload_file(self, data: bytes, path: str, content_type: Optional[str] = None) -> str:
        """Upload file to GCS."""
        blob = self.bucket.blob(path)

        if content_type:
            blob.upload_from_string(data, content_type=content_type)
        else:
            blob.upload_from_string(data)

        return f"gs://{self.bucket.name}/{path}"

    async def upload_stream(
        self, stream: io.BytesIO, path: str, content_type: Optional[str] = None
    ) -> str:
        """Upload from stream to GCS."""
        data = stream.getvalue()
        return await self.upload_file(data, path, content_type)

    async def download_file(self, path: str) -> Optional[bytes]:
        """Download file from GCS."""
        try:
            blob = self.bucket.blob(path)
            return blob.download_as_bytes()
        except Exception:
            return None

    async def delete_file(self, path: str) -> bool:
        """Delete file from GCS."""
        try:
            blob = self.bucket.blob(path)
            blob.delete()
            return True
        except Exception:
            return False

    async def file_exists(self, path: str) -> bool:
        """Check if file exists in GCS."""
        blob = self.bucket.blob(path)
        return blob.exists()
