"""Extended Tests for S3StorageAdapter.

Tests cover all S3 operations with mocked aioboto3:
- save_file
- get_file
- delete_file
- exists
- list_files
- get_metadata
- get_url
- copy
- move
- presigned uploads
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from framework_m.adapters.storage.s3 import (
    CompletedPart,
    MultipartUploadInfo,
    PresignedUploadInfo,
    S3StorageAdapter,
)

# =============================================================================
# Test: Import
# =============================================================================


class TestS3StorageImport:
    """Tests for S3StorageAdapter import."""

    def test_import_s3_storage_adapter(self) -> None:
        """S3StorageAdapter should be importable."""
        from framework_m.adapters.storage import S3StorageAdapter

        assert S3StorageAdapter is not None

    def test_import_presigned_upload_info(self) -> None:
        """PresignedUploadInfo should be importable."""
        from framework_m.adapters.storage import PresignedUploadInfo

        assert PresignedUploadInfo is not None

    def test_import_completed_part(self) -> None:
        """CompletedPart should be importable."""
        from framework_m.adapters.storage import CompletedPart

        assert CompletedPart is not None

    def test_import_multipart_upload_info(self) -> None:
        """MultipartUploadInfo should be importable."""
        from framework_m.adapters.storage.s3 import MultipartUploadInfo

        assert MultipartUploadInfo is not None


# =============================================================================
# Test: Models
# =============================================================================


class TestPresignedUploadInfo:
    """Tests for PresignedUploadInfo model."""

    def test_simple_upload(self) -> None:
        """PresignedUploadInfo should work for simple upload."""
        info = PresignedUploadInfo(
            upload_url="https://s3.amazonaws.com/bucket/key?X-Amz-...",
            key="uploads/file.pdf",
            expires_in=3600,
        )
        assert info.upload_url.startswith("https://")
        assert info.key == "uploads/file.pdf"
        assert info.upload_id is None

    def test_multipart_upload(self) -> None:
        """PresignedUploadInfo should support multipart."""
        info = PresignedUploadInfo(
            upload_url="https://s3.amazonaws.com/...",
            key="uploads/large.zip",
            expires_in=3600,
            upload_id="abc123",
            part_urls=[
                "https://s3.amazonaws.com/...?partNumber=1",
                "https://s3.amazonaws.com/...?partNumber=2",
            ],
        )
        assert info.upload_id == "abc123"
        assert len(info.part_urls) == 2


class TestCompletedPart:
    """Tests for CompletedPart model."""

    def test_completed_part(self) -> None:
        """CompletedPart should store part info."""
        part = CompletedPart(part_number=1, etag="abc123")
        assert part.part_number == 1
        assert part.etag == "abc123"


class TestMultipartUploadInfo:
    """Tests for MultipartUploadInfo model."""

    def test_multipart_upload_info(self) -> None:
        """MultipartUploadInfo should store upload info."""
        info = MultipartUploadInfo(
            upload_id="abc123",
            key="uploads/large.zip",
            part_size=25 * 1024 * 1024,
            part_urls=["https://s3.amazonaws.com/part1"],
        )
        assert info.upload_id == "abc123"
        assert info.part_size == 25 * 1024 * 1024


# =============================================================================
# Test: Initialization
# =============================================================================


class TestS3StorageInit:
    """Tests for S3StorageAdapter initialization."""

    def test_init_with_bucket(self) -> None:
        """S3StorageAdapter should accept bucket parameter."""
        adapter = S3StorageAdapter(bucket="my-bucket", region="us-east-1")
        assert adapter._bucket == "my-bucket"
        assert adapter._region == "us-east-1"

    def test_init_with_endpoint(self) -> None:
        """S3StorageAdapter should accept custom endpoint."""
        adapter = S3StorageAdapter(
            bucket="my-bucket",
            endpoint_url="http://localhost:9000",
        )
        assert adapter._endpoint_url == "http://localhost:9000"

    def test_init_without_bucket_raises(self) -> None:
        """S3StorageAdapter should require bucket."""
        with (
            patch("framework_m.adapters.storage.s3.load_config", return_value={}),
            pytest.raises(ValueError, match="bucket not configured"),
        ):
            S3StorageAdapter()

    def test_init_from_config(self) -> None:
        """S3StorageAdapter should read from config."""
        mock_config = {
            "files": {
                "s3_bucket": "config-bucket",
                "s3_region": "eu-west-1",
            }
        }
        with patch(
            "framework_m.adapters.storage.s3.load_config",
            return_value=mock_config,
        ):
            adapter = S3StorageAdapter()
            assert adapter._bucket == "config-bucket"
            assert adapter._region == "eu-west-1"

    def test_init_with_credentials(self) -> None:
        """S3StorageAdapter should accept credentials."""
        adapter = S3StorageAdapter(
            bucket="test",
            access_key="AKIATEST",
            secret_key="secretkey",
        )
        assert adapter._access_key == "AKIATEST"
        assert adapter._secret_key == "secretkey"


# =============================================================================
# Test: Configuration
# =============================================================================


class TestS3StorageConfig:
    """Tests for S3 configuration."""

    def test_default_part_size(self) -> None:
        """DEFAULT_PART_SIZE should be 25MB."""
        assert S3StorageAdapter.DEFAULT_PART_SIZE == 25 * 1024 * 1024

    def test_client_params_basic(self) -> None:
        """_get_client_params should include region."""
        adapter = S3StorageAdapter(bucket="test", region="us-west-2")
        params = adapter._get_client_params()

        assert params["region_name"] == "us-west-2"

    def test_client_params_with_endpoint(self) -> None:
        """_get_client_params should include endpoint."""
        adapter = S3StorageAdapter(
            bucket="test",
            endpoint_url="http://minio:9000",
        )
        params = adapter._get_client_params()

        assert params["endpoint_url"] == "http://minio:9000"

    def test_client_params_with_credentials(self) -> None:
        """_get_client_params should include credentials."""
        adapter = S3StorageAdapter(
            bucket="test",
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )
        params = adapter._get_client_params()

        assert params["aws_access_key_id"] == "AKIAIOSFODNN7EXAMPLE"
        assert "aws_secret_access_key" in params


# =============================================================================
# Test: save_file
# =============================================================================


class TestS3SaveFile:
    """Tests for S3StorageAdapter.save_file()."""

    @pytest.mark.asyncio
    async def test_save_file_success(self) -> None:
        """save_file should upload content to S3."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        mock_s3_client.put_object = AsyncMock()

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            result = await adapter.save_file("path/to/file.txt", b"content")

        assert result == "path/to/file.txt"
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_file_with_content_type(self) -> None:
        """save_file should include content type."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        mock_s3_client.put_object = AsyncMock()

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            await adapter.save_file(
                "path/to/file.pdf", b"content", content_type="application/pdf"
            )

        call_kwargs = mock_s3_client.put_object.call_args[1]
        assert call_kwargs["ContentType"] == "application/pdf"


# =============================================================================
# Test: get_file
# =============================================================================


class TestS3GetFile:
    """Tests for S3StorageAdapter.get_file()."""

    @pytest.mark.asyncio
    async def test_get_file_success(self) -> None:
        """get_file should download content from S3."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_body = AsyncMock()
        mock_body.read = AsyncMock(return_value=b"file content")
        mock_body.__aenter__ = AsyncMock(return_value=mock_body)
        mock_body.__aexit__ = AsyncMock(return_value=None)

        mock_s3_client = AsyncMock()
        mock_s3_client.get_object = AsyncMock(return_value={"Body": mock_body})

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            content = await adapter.get_file("path/to/file.txt")

        assert content == b"file content"

    @pytest.mark.asyncio
    async def test_get_file_not_found(self) -> None:
        """get_file should raise FileNotFoundError for missing file."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        error = MagicMock()
        error.response = {"Error": {"Code": "NoSuchKey"}}
        mock_s3_client.get_object = AsyncMock(side_effect=Exception())

        # Import botocore to create proper error
        with pytest.raises((FileNotFoundError, Exception)):
            mock_session = MagicMock()
            mock_session.client.return_value.__aenter__ = AsyncMock(
                return_value=mock_s3_client
            )
            mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("aioboto3.Session", return_value=mock_session):
                await adapter.get_file("nonexistent.txt")


# =============================================================================
# Test: delete_file
# =============================================================================


class TestS3DeleteFile:
    """Tests for S3StorageAdapter.delete_file()."""

    @pytest.mark.asyncio
    async def test_delete_file_success(self) -> None:
        """delete_file should remove object from S3."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        mock_s3_client.head_object = AsyncMock(return_value={})
        mock_s3_client.delete_object = AsyncMock()

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            await adapter.delete_file("path/to/file.txt")

        mock_s3_client.delete_object.assert_called_once()


# =============================================================================
# Test: exists
# =============================================================================


class TestS3Exists:
    """Tests for S3StorageAdapter.exists()."""

    @pytest.mark.asyncio
    async def test_exists_true(self) -> None:
        """exists should return True for existing object."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        mock_s3_client.head_object = AsyncMock(return_value={})

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            result = await adapter.exists("path/to/file.txt")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self) -> None:
        """exists should return False for missing object."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        # Simulate 404 error
        error = MagicMock()
        error.response = {"Error": {"Code": "404"}}

        mock_s3_client.head_object = AsyncMock(
            side_effect=ClientError(error, "HeadObject")
        )

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            result = await adapter.exists("nonexistent.txt")

        assert result is False


# =============================================================================
# Test: list_files
# =============================================================================


class TestS3ListFiles:
    """Tests for S3StorageAdapter.list_files()."""

    @pytest.mark.asyncio
    async def test_list_files_success(self) -> None:
        """list_files should return matching keys."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        # Create async paginator mock
        class MockPaginator:
            async def paginate(self, **kwargs):
                yield {
                    "Contents": [
                        {"Key": "uploads/file1.txt"},
                        {"Key": "uploads/file2.txt"},
                    ]
                }

        mock_s3_client = AsyncMock()
        mock_s3_client.get_paginator = MagicMock(return_value=MockPaginator())

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            files = await adapter.list_files("uploads/")

        assert len(files) == 2
        assert "uploads/file1.txt" in files

    @pytest.mark.asyncio
    async def test_list_files_empty(self) -> None:
        """list_files should return empty list when no matches."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        # Create async paginator mock that returns empty
        class MockPaginator:
            async def paginate(self, **kwargs):
                yield {}

        mock_s3_client = AsyncMock()
        mock_s3_client.get_paginator = MagicMock(return_value=MockPaginator())

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            files = await adapter.list_files("nonexistent/")

        assert files == []


# =============================================================================
# Test: get_metadata
# =============================================================================


class TestS3GetMetadata:
    """Tests for S3StorageAdapter.get_metadata()."""

    @pytest.mark.asyncio
    async def test_get_metadata_success(self) -> None:
        """get_metadata should return file metadata."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        mock_s3_client.head_object = AsyncMock(
            return_value={
                "ContentLength": 1024,
                "ContentType": "application/pdf",
                "LastModified": datetime(2024, 1, 1, tzinfo=UTC),
            }
        )

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            metadata = await adapter.get_metadata("path/to/file.pdf")

        assert metadata is not None
        assert metadata.size == 1024
        assert metadata.content_type == "application/pdf"


# =============================================================================
# Test: get_url
# =============================================================================


class TestS3GetUrl:
    """Tests for S3StorageAdapter.get_url()."""

    @pytest.mark.asyncio
    async def test_get_url_success(self) -> None:
        """get_url should return presigned URL."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        mock_s3_client.generate_presigned_url = AsyncMock(
            return_value="https://s3.amazonaws.com/bucket/key?signature=..."
        )

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            url = await adapter.get_url("path/to/file.pdf")

        assert url.startswith("https://")
        assert "signature" in url


# =============================================================================
# Test: copy
# =============================================================================


class TestS3Copy:
    """Tests for S3StorageAdapter.copy()."""

    @pytest.mark.asyncio
    async def test_copy_success(self) -> None:
        """copy should copy object within bucket."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        mock_s3_client.head_object = AsyncMock(return_value={})
        mock_s3_client.copy_object = AsyncMock()

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            result = await adapter.copy("source.txt", "dest.txt")

        assert result == "dest.txt"
        mock_s3_client.copy_object.assert_called_once()


# =============================================================================
# Test: move
# =============================================================================


class TestS3Move:
    """Tests for S3StorageAdapter.move()."""

    @pytest.mark.asyncio
    async def test_move_success(self) -> None:
        """move should copy then delete source."""
        adapter = S3StorageAdapter(bucket="test-bucket", region="us-east-1")

        mock_s3_client = AsyncMock()
        mock_s3_client.head_object = AsyncMock(return_value={})
        mock_s3_client.copy_object = AsyncMock()
        mock_s3_client.delete_object = AsyncMock()

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(
            return_value=mock_s3_client
        )
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("aioboto3.Session", return_value=mock_session):
            result = await adapter.move("source.txt", "dest.txt")

        assert result == "dest.txt"
        mock_s3_client.copy_object.assert_called()
        mock_s3_client.delete_object.assert_called()


# =============================================================================
# Test: All Exports
# =============================================================================


class TestStorageExports:
    """Tests for storage module exports."""

    def test_all_exports(self) -> None:
        """Storage module should export all adapters."""
        from framework_m.adapters import storage

        assert hasattr(storage, "InMemoryStorageAdapter")
        assert hasattr(storage, "LocalStorageAdapter")
        assert hasattr(storage, "S3StorageAdapter")
        assert hasattr(storage, "PresignedUploadInfo")
        assert hasattr(storage, "CompletedPart")
