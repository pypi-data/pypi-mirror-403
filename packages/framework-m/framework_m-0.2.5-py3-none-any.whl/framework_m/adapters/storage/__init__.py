"""Storage Adapters - File storage implementations.

This module provides storage adapters for different backends:
- InMemoryStorageAdapter: In-memory storage for testing
- LocalStorageAdapter: Filesystem-based storage for development/Indie mode
- S3StorageAdapter: AWS S3 / compatible object storage for production

Configuration in framework_config.toml:
    [files]
    storage_backend = "local"  # or "s3"
    storage_path = "./uploads"  # for local
    s3_bucket = "my-bucket"     # for s3
    s3_region = "us-east-1"     # for s3
"""

from framework_m.adapters.storage.local import LocalStorageAdapter
from framework_m.adapters.storage.memory import InMemoryStorageAdapter
from framework_m.adapters.storage.s3 import (
    CompletedPart,
    MultipartUploadInfo,
    PresignedUploadInfo,
    S3StorageAdapter,
)

__all__ = [
    "CompletedPart",
    "InMemoryStorageAdapter",
    "LocalStorageAdapter",
    "MultipartUploadInfo",
    "PresignedUploadInfo",
    "S3StorageAdapter",
]
