import os
from pathlib import Path
import boto3
from botocore.client import Config
from google.cloud import storage
import structlog
from rag.config.settings import get_settings

logger = structlog.get_logger()


class StorageClient:
    """Hybrid storage client supporting local, MinIO, and GCS storage backends."""

    def __init__(self):
        self.settings = get_settings()
        self.provider = self.settings.storage_provider.lower()
        logger.info("initializing_storage_client", provider=self.provider)

        # Base bucket name is always normalized to resolve '-' vs '_' differences if any
        self.bucket_name = self.settings.gcs_bucket_name.replace("_", "-")

        if self.provider == "gcs":
            self.gcs_client = storage.Client()
        elif self.provider == "minio":
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.settings.minio_endpoint,
                aws_access_key_id=self.settings.minio_access_key,
                aws_secret_access_key=self.settings.minio_secret_key,
                config=Config(signature_version="s3v4"),
                region_name="us-east-1",  # default dummy region for minio
            )
        elif self.provider == "local":
            # Dynamically compute local storage directory relative to project root
            self.local_dir = Path(__file__).parents[4] / "data" / "storage_local"
            self.local_dir.mkdir(parents=True, exist_ok=True)
        else:
            raise ValueError(f"Unsupported storage provider: {self.provider}")

    def upload_file(self, local_path: str | Path, remote_name: str) -> str:
        """Upload a file to the storage provider.

        Returns:
            A string representing the storage URI/path.
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file does not exist: {local_path}")

        logger.info("uploading_file", provider=self.provider, local_path=str(local_path), remote_name=remote_name)

        if self.provider == "gcs":
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(remote_name)
            blob.upload_from_filename(str(local_path))
            return f"gs://{self.bucket_name}/{remote_name}"

        elif self.provider == "minio":
            self.s3_client.upload_file(str(local_path), self.bucket_name, remote_name)
            return f"s3://{self.bucket_name}/{remote_name}"

        elif self.provider == "local":
            dest_path = self.local_dir / remote_name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(local_path, dest_path)
            return str(dest_path)

    def download_file(self, remote_name: str, local_destination: str | Path) -> None:
        """Download a file from the storage provider to local destination."""
        local_destination = Path(local_destination)
        local_destination.parent.mkdir(parents=True, exist_ok=True)

        logger.info("downloading_file", provider=self.provider, remote_name=remote_name, dest=str(local_destination))

        if self.provider == "gcs":
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(remote_name)
            blob.download_to_filename(str(local_destination))

        elif self.provider == "minio":
            self.s3_client.download_file(self.bucket_name, remote_name, str(local_destination))

        elif self.provider == "local":
            src_path = self.local_dir / remote_name
            if not src_path.exists():
                raise FileNotFoundError(f"Remote (local dir) file does not exist: {src_path}")
            import shutil
            shutil.copy2(src_path, local_destination)

    def list_files(self) -> list[str]:
        """List files in the storage bucket/directory."""
        logger.info("listing_files", provider=self.provider)

        if self.provider == "gcs":
            bucket = self.gcs_client.bucket(self.bucket_name)
            blobs = bucket.list_blobs()
            return [blob.name for blob in blobs]

        elif self.provider == "minio":
            try:
                response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
                return [obj["Key"] for obj in response.get("Contents", [])]
            except Exception as e:
                logger.error("minio_list_failed", error=str(e))
                return []

        elif self.provider == "local":
            return [str(p.relative_to(self.local_dir)) for p in self.local_dir.rglob("*") if p.is_file()]

    def delete_file(self, remote_name: str) -> None:
        """Delete a file from the storage provider."""
        logger.info("deleting_file", provider=self.provider, remote_name=remote_name)

        if self.provider == "gcs":
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(remote_name)
            blob.delete()

        elif self.provider == "minio":
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=remote_name)

        elif self.provider == "local":
            file_path = self.local_dir / remote_name
            if file_path.exists():
                file_path.unlink()
