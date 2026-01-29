"""S3 Storage Adapter - AWS S3 / compatible object storage implementation.

This module provides S3StorageAdapter for storing files in S3 or compatible
object storage (MinIO, DigitalOcean Spaces, etc.).

Features:
- Presigned URLs for direct client uploads (PUT method)
- Multipart upload for large files (>5MB)
- Presigned download URLs with expiration
- Async operations via aioboto3

Configuration in framework_config.toml:
    [files]
    storage_backend = "s3"
    s3_bucket = "my-app-files"
    s3_region = "us-east-1"
    s3_endpoint = null  # For S3-compatible services
    large_file_threshold = "5MB"

Example:
    storage = S3StorageAdapter(bucket="my-bucket", region="us-east-1")

    # Direct upload flow for large files:
    # 1. Get presigned URL
    url_info = await storage.create_presigned_upload("large-file.zip")
    # 2. Client uploads directly to S3 using PUT
    # 3. Confirm upload
    await storage.complete_upload("large-file.zip")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from typing import Any

from framework_m.cli.config import load_config
from framework_m.core.interfaces.storage import FileMetadata, StorageProtocol

# =============================================================================
# Presigned Upload Models
# =============================================================================


@dataclass
class PresignedUploadInfo:
    """Information for presigned upload.

    Attributes:
        upload_url: Presigned PUT URL for direct upload
        upload_id: Multipart upload ID (for large files)
        key: S3 object key
        expires_in: URL expiration in seconds
        part_urls: List of presigned URLs for multipart parts
    """

    upload_url: str
    key: str
    expires_in: int = 3600
    upload_id: str | None = None
    part_urls: list[str] = field(default_factory=list)


@dataclass
class MultipartUploadInfo:
    """Information for multipart upload.

    Attributes:
        upload_id: S3 multipart upload ID
        key: S3 object key
        part_size: Size of each part in bytes
        part_urls: Presigned URLs for each part
    """

    upload_id: str
    key: str
    part_size: int
    part_urls: list[str]


@dataclass
class CompletedPart:
    """Completed part information for multipart upload.

    Attributes:
        part_number: 1-indexed part number
        etag: ETag returned by S3 after part upload
    """

    part_number: int
    etag: str


# =============================================================================
# S3 Storage Adapter
# =============================================================================


class S3StorageAdapter(StorageProtocol):
    """AWS S3 / compatible object storage adapter.

    Implements StorageProtocol for S3-based storage with:
    - Presigned URLs for direct client uploads
    - Multipart upload for large files
    - Presigned download URLs

    Attributes:
        bucket: S3 bucket name
        region: AWS region
        endpoint_url: Custom endpoint for S3-compatible services

    Example:
        storage = S3StorageAdapter(
            bucket="my-bucket",
            region="us-east-1",
        )

        # For small files (< 5MB)
        await storage.save_file("small.pdf", content)

        # For large files - use presigned upload
        info = await storage.create_presigned_upload(
            "large.zip",
            content_type="application/zip",
            file_size=100_000_000,  # 100MB
        )
        # Client uploads to info.upload_url
    """

    # Default part size for multipart: 25MB (AWS minimum is 5MB, but 25MB reduces overhead)
    DEFAULT_PART_SIZE = 25 * 1024 * 1024

    def __init__(
        self,
        bucket: str | None = None,
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        """Initialize the S3 storage adapter.

        Args:
            bucket: S3 bucket name (from config if None)
            region: AWS region (from config if None)
            endpoint_url: Custom endpoint for S3-compatible services
            access_key: AWS access key (from env/config if None)
            secret_key: AWS secret key (from env/config if None)
        """
        config = self._load_config()

        self._bucket = bucket or config.get("s3_bucket", "")
        self._region = region or config.get("s3_region", "us-east-1")
        self._endpoint_url = endpoint_url or config.get("s3_endpoint")
        self._access_key = access_key
        self._secret_key = secret_key

        if not self._bucket:
            raise ValueError(
                "S3 bucket not configured. "
                "Set [files].s3_bucket in framework_config.toml"
            )

    def _load_config(self) -> dict[str, Any]:
        """Load S3 configuration from config file."""
        config = load_config()
        files_config: dict[str, Any] = config.get("files", {})
        return files_config

    def _get_client_params(self) -> dict[str, Any]:
        """Get boto3 client parameters."""
        params: dict[str, Any] = {
            "region_name": self._region,
        }
        if self._endpoint_url:
            params["endpoint_url"] = self._endpoint_url
        if self._access_key and self._secret_key:
            params["aws_access_key_id"] = self._access_key
            params["aws_secret_access_key"] = self._secret_key
        return params

    async def save_file(
        self,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        """Upload file content to S3.

        For small files only. For large files (>5MB), use
        create_presigned_upload() for direct client upload.

        Args:
            path: S3 object key
            content: File content as bytes
            content_type: Optional MIME type

        Returns:
            The S3 object key
        """
        try:
            import aioboto3  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        session = aioboto3.Session()
        params = self._get_client_params()

        async with session.client("s3", **params) as s3:
            put_params: dict[str, Any] = {
                "Bucket": self._bucket,
                "Key": path,
                "Body": content,
            }
            if content_type:
                put_params["ContentType"] = content_type

            await s3.put_object(**put_params)

        return path

    async def get_file(self, path: str) -> bytes:
        """Download file from S3.

        Args:
            path: S3 object key

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If object doesn't exist
        """
        try:
            import aioboto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        session = aioboto3.Session()
        params = self._get_client_params()

        async with session.client("s3", **params) as s3:
            try:
                response = await s3.get_object(Bucket=self._bucket, Key=path)
                async with response["Body"] as stream:
                    content: bytes = await stream.read()
                    return content
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    raise FileNotFoundError(f"File not found: {path}") from e
                raise

    async def delete_file(self, path: str) -> None:
        """Delete file from S3.

        Args:
            path: S3 object key

        Raises:
            FileNotFoundError: If object doesn't exist
        """
        try:
            import aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        # Check existence first
        if not await self.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        session = aioboto3.Session()
        params = self._get_client_params()

        async with session.client("s3", **params) as s3:
            await s3.delete_object(Bucket=self._bucket, Key=path)

    async def exists(self, path: str) -> bool:
        """Check if object exists in S3.

        Args:
            path: S3 object key

        Returns:
            True if object exists
        """
        try:
            import aioboto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        session = aioboto3.Session()
        params = self._get_client_params()

        async with session.client("s3", **params) as s3:
            try:
                await s3.head_object(Bucket=self._bucket, Key=path)
                return True
            except ClientError:
                return False

    async def list_files(self, prefix: str) -> list[str]:
        """List objects matching a prefix.

        Args:
            prefix: Key prefix to filter by

        Returns:
            List of matching object keys
        """
        try:
            import aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        session = aioboto3.Session()
        params = self._get_client_params()

        result: list[str] = []
        async with session.client("s3", **params) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    result.append(obj["Key"])

        return result

    async def get_metadata(self, path: str) -> FileMetadata | None:
        """Get object metadata from S3.

        Args:
            path: S3 object key

        Returns:
            FileMetadata if object exists, None otherwise
        """
        try:
            import aioboto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        session = aioboto3.Session()
        params = self._get_client_params()

        async with session.client("s3", **params) as s3:
            try:
                response = await s3.head_object(Bucket=self._bucket, Key=path)
                return FileMetadata(
                    path=path,
                    size=response["ContentLength"],
                    modified=response["LastModified"].replace(tzinfo=UTC),
                    content_type=response.get("ContentType"),
                    etag=response.get("ETag", "").strip('"'),
                )
            except ClientError:
                return None

    async def get_url(self, path: str, expires: int = 3600) -> str:
        """Generate presigned download URL.

        Args:
            path: S3 object key
            expires: URL expiration in seconds (default: 1 hour)

        Returns:
            Presigned URL for download
        """
        try:
            import aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        session = aioboto3.Session()
        params = self._get_client_params()

        async with session.client("s3", **params) as s3:
            url: str = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": path},
                ExpiresIn=expires,
            )
            return url

    async def copy(self, src: str, dest: str) -> str:
        """Copy object within S3.

        Args:
            src: Source object key
            dest: Destination object key

        Returns:
            Destination key

        Raises:
            FileNotFoundError: If source doesn't exist
        """
        try:
            import aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        if not await self.exists(src):
            raise FileNotFoundError(f"Source file not found: {src}")

        session = aioboto3.Session()
        params = self._get_client_params()

        async with session.client("s3", **params) as s3:
            await s3.copy_object(
                Bucket=self._bucket,
                Key=dest,
                CopySource={"Bucket": self._bucket, "Key": src},
            )

        return dest

    async def move(self, src: str, dest: str) -> str:
        """Move object within S3 (copy + delete).

        Args:
            src: Source object key
            dest: Destination object key

        Returns:
            Destination key

        Raises:
            FileNotFoundError: If source doesn't exist
        """
        await self.copy(src, dest)
        await self.delete_file(src)
        return dest

    # =========================================================================
    # Presigned Upload Methods (Direct Client Upload)
    # =========================================================================

    async def create_presigned_upload(
        self,
        path: str,
        content_type: str | None = None,
        file_size: int | None = None,
        expires: int = 3600,
    ) -> PresignedUploadInfo:
        """Create presigned URL for direct client upload.

        For files < 5MB: Returns single PUT URL.
        For files >= 5MB: Returns multipart upload info with part URLs.

        Args:
            path: S3 object key
            content_type: MIME type for the upload
            file_size: Total file size (required for multipart)
            expires: URL expiration in seconds

        Returns:
            PresignedUploadInfo with upload URL(s)
        """
        try:
            import aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        session = aioboto3.Session()
        params = self._get_client_params()

        # Determine if multipart is needed
        use_multipart = file_size is not None and file_size >= self.DEFAULT_PART_SIZE

        async with session.client("s3", **params) as s3:
            if use_multipart and file_size is not None:
                return await self._create_multipart_upload(
                    s3, path, content_type, file_size, expires
                )
            else:
                return await self._create_simple_upload(s3, path, content_type, expires)

    async def _create_simple_upload(
        self,
        s3: Any,
        path: str,
        content_type: str | None,
        expires: int,
    ) -> PresignedUploadInfo:
        """Create presigned PUT URL for simple upload."""
        params: dict[str, Any] = {"Bucket": self._bucket, "Key": path}
        if content_type:
            params["ContentType"] = content_type

        url: str = await s3.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expires,
        )

        return PresignedUploadInfo(
            upload_url=url,
            key=path,
            expires_in=expires,
        )

    async def _create_multipart_upload(
        self,
        s3: Any,
        path: str,
        content_type: str | None,
        file_size: int,
        expires: int,
    ) -> PresignedUploadInfo:
        """Create multipart upload with presigned part URLs."""
        # Initiate multipart upload
        create_params: dict[str, Any] = {"Bucket": self._bucket, "Key": path}
        if content_type:
            create_params["ContentType"] = content_type

        response = await s3.create_multipart_upload(**create_params)
        upload_id: str = response["UploadId"]

        # Calculate number of parts
        num_parts = (file_size + self.DEFAULT_PART_SIZE - 1) // self.DEFAULT_PART_SIZE

        # Generate presigned URLs for each part
        part_urls: list[str] = []
        for part_num in range(1, num_parts + 1):
            url: str = await s3.generate_presigned_url(
                "upload_part",
                Params={
                    "Bucket": self._bucket,
                    "Key": path,
                    "UploadId": upload_id,
                    "PartNumber": part_num,
                },
                ExpiresIn=expires,
            )
            part_urls.append(url)

        return PresignedUploadInfo(
            upload_url=part_urls[0] if part_urls else "",
            key=path,
            expires_in=expires,
            upload_id=upload_id,
            part_urls=part_urls,
        )

    async def complete_multipart_upload(
        self,
        path: str,
        upload_id: str,
        parts: list[CompletedPart],
    ) -> str:
        """Complete a multipart upload.

        Called after all parts have been uploaded successfully.

        Args:
            path: S3 object key
            upload_id: Multipart upload ID
            parts: List of completed parts with ETags

        Returns:
            Final object key
        """
        try:
            import aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        session = aioboto3.Session()
        params = self._get_client_params()

        async with session.client("s3", **params) as s3:
            await s3.complete_multipart_upload(
                Bucket=self._bucket,
                Key=path,
                UploadId=upload_id,
                MultipartUpload={
                    "Parts": [
                        {"PartNumber": p.part_number, "ETag": p.etag} for p in parts
                    ]
                },
            )

        return path

    async def abort_multipart_upload(self, path: str, upload_id: str) -> None:
        """Abort a multipart upload.

        Cleans up incomplete multipart upload.

        Args:
            path: S3 object key
            upload_id: Multipart upload ID
        """
        try:
            import aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 package not installed. Run: pip install aioboto3"
            ) from None

        session = aioboto3.Session()
        params = self._get_client_params()

        async with session.client("s3", **params) as s3:
            await s3.abort_multipart_upload(
                Bucket=self._bucket,
                Key=path,
                UploadId=upload_id,
            )


__all__ = [
    "CompletedPart",
    "MultipartUploadInfo",
    "PresignedUploadInfo",
    "S3StorageAdapter",
]
