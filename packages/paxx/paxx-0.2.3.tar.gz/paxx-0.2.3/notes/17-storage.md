# Object Storage (S3) Implementation Plan

S3-compatible object storage for file uploads, media, and user-generated content in Paxx-generated projects.

---

## Overview

Object storage is essential for handling file uploads, media assets, and user-generated content. The implementation provides:

- **Abstract StorageBackend interface** - swap implementations without code changes
- **Local filesystem backend** - for development (no external dependencies)
- **S3-compatible backend** - for production (AWS S3, MinIO, DigitalOcean Spaces, etc.)
- **MinIO in Docker** - for local S3-compatible testing

---

## Implementation Structure

```
src/paxx/infra/storage/
├── __init__.py
├── config.py
├── dependencies.txt
├── docker_service.yml          # MinIO service
└── templates/
    └── storage.py.jinja        # StorageBackend interface + implementations
```

---

## 1. Config (`config.py`)

```python
"""Object storage infrastructure configuration."""

from dataclasses import dataclass, field


@dataclass
class InfraConfig:
    """Configuration for object storage infrastructure."""

    name: str = "storage"
    docker_service: str = "minio"
    core_files: list[str] = field(default_factory=lambda: ["storage.py"])
    dependencies: list[str] = field(
        default_factory=lambda: ["aioboto3>=13.0", "aiofiles>=24.0"]
    )
    env_vars: dict[str, str] = field(
        default_factory=lambda: {
            "STORAGE_BACKEND": "local",
            "STORAGE_LOCAL_PATH": "./uploads",
            "STORAGE_S3_BUCKET": "",
            "STORAGE_S3_REGION": "us-east-1",
            "STORAGE_S3_ENDPOINT_URL": "",
            "STORAGE_S3_ACCESS_KEY": "",
            "STORAGE_S3_SECRET_KEY": "",
        }
    )
```

**Notes:**
- `STORAGE_BACKEND` can be `local` or `s3`
- `STORAGE_S3_ENDPOINT_URL` is optional - set for MinIO or S3-compatible services, leave empty for AWS S3
- Local backend is default for easy development

---

## 2. Dependencies (`dependencies.txt`)

```
aioboto3>=13.0
aiofiles>=24.0
```

**Notes:**
- `aioboto3` - async wrapper around boto3 for S3 operations
- `aiofiles` - async file I/O for local backend

---

## 3. Docker Service (`docker_service.yml`)

```yaml
minio:
  image: minio/minio:latest
  command: server /data --console-address ":9001"
  ports:
    - "9000:9000"
    - "9001:9001"
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  volumes:
    - minio_data:/data
  healthcheck:
    test: ["CMD", "mc", "ready", "local"]
    interval: 5s
    timeout: 5s
    retries: 5
```

**Notes:**
- Port 9000: S3-compatible API
- Port 9001: MinIO web console
- Default credentials: `minioadmin` / `minioadmin`
- Users can access the web console at http://localhost:9001

---

## 4. Storage Template (`templates/storage.py.jinja`)

```python
"""
Object storage with pluggable backends.

Supports local filesystem (development) and S3-compatible storage (production).

Usage:
    from core.storage import get_storage

    storage = get_storage()

    # Upload a file
    url = await storage.upload("avatars/user-123.jpg", file_content, content_type="image/jpeg")

    # Download a file
    content = await storage.download("avatars/user-123.jpg")

    # Delete a file
    await storage.delete("avatars/user-123.jpg")

    # Generate a presigned URL (S3 only)
    url = await storage.presign("avatars/user-123.jpg", expires_in=3600)
"""

import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

from settings import settings

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str | None = None,
    ) -> str:
        """
        Upload a file to storage.

        Args:
            key: Storage key (path-like, e.g., "avatars/user-123.jpg")
            data: File content as bytes or file-like object
            content_type: MIME type of the file

        Returns:
            URL or path to the uploaded file
        """
        ...

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """
        Download a file from storage.

        Args:
            key: Storage key

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete a file from storage.

        Args:
            key: Storage key
        """
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            key: Storage key

        Returns:
            True if file exists, False otherwise
        """
        ...

    async def presign(self, key: str, expires_in: int = 3600) -> str | None:
        """
        Generate a presigned URL for temporary access.

        Args:
            key: Storage key
            expires_in: URL expiration time in seconds

        Returns:
            Presigned URL or None if not supported
        """
        return None


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend for development."""

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """Get full path for a key, ensuring it's within base_path."""
        path = (self.base_path / key).resolve()
        if not str(path).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Invalid key: {key}")
        return path

    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str | None = None,
    ) -> str:
        import aiofiles

        path = self._get_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, bytes):
            async with aiofiles.open(path, "wb") as f:
                await f.write(data)
        else:
            async with aiofiles.open(path, "wb") as f:
                await f.write(data.read())

        logger.debug(f"Uploaded file to local storage: {key}")
        return str(path)

    async def download(self, key: str) -> bytes:
        import aiofiles

        path = self._get_path(key)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete(self, key: str) -> None:
        path = self._get_path(key)
        if path.exists():
            path.unlink()
            logger.debug(f"Deleted file from local storage: {key}")

    async def exists(self, key: str) -> bool:
        path = self._get_path(key)
        return path.exists()


class S3StorageBackend(StorageBackend):
    """S3-compatible storage backend for production."""

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
    ):
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url or None
        self.access_key = access_key
        self.secret_key = secret_key

    def _get_session(self):
        """Get aioboto3 session with configured credentials."""
        import aioboto3

        return aioboto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )

    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str | None = None,
    ) -> str:
        session = self._get_session()

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        async with session.client("s3", endpoint_url=self.endpoint_url) as s3:
            if isinstance(data, bytes):
                await s3.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=data,
                    **extra_args,
                )
            else:
                await s3.upload_fileobj(
                    data,
                    self.bucket,
                    key,
                    ExtraArgs=extra_args if extra_args else None,
                )

        logger.debug(f"Uploaded file to S3: {key}")

        # Return URL
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket}/{key}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    async def download(self, key: str) -> bytes:
        session = self._get_session()

        async with session.client("s3", endpoint_url=self.endpoint_url) as s3:
            try:
                response = await s3.get_object(Bucket=self.bucket, Key=key)
                async with response["Body"] as stream:
                    return await stream.read()
            except s3.exceptions.NoSuchKey:
                raise FileNotFoundError(f"File not found: {key}")

    async def delete(self, key: str) -> None:
        session = self._get_session()

        async with session.client("s3", endpoint_url=self.endpoint_url) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)
            logger.debug(f"Deleted file from S3: {key}")

    async def exists(self, key: str) -> bool:
        session = self._get_session()

        async with session.client("s3", endpoint_url=self.endpoint_url) as s3:
            try:
                await s3.head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False

    async def presign(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for temporary access."""
        session = self._get_session()

        async with session.client("s3", endpoint_url=self.endpoint_url) as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url


@lru_cache
def get_storage() -> StorageBackend:
    """
    Get the configured storage backend.

    Returns LocalStorageBackend or S3StorageBackend based on settings.
    """
    backend = settings.storage_backend.lower()

    if backend == "local":
        return LocalStorageBackend(settings.storage_local_path)

    elif backend == "s3":
        if not settings.storage_s3_bucket:
            raise ValueError("STORAGE_S3_BUCKET is required for S3 backend")

        return S3StorageBackend(
            bucket=settings.storage_s3_bucket,
            region=settings.storage_s3_region,
            endpoint_url=settings.storage_s3_endpoint_url or None,
            access_key=settings.storage_s3_access_key or None,
            secret_key=settings.storage_s3_secret_key or None,
        )

    else:
        raise ValueError(f"Unknown storage backend: {backend}")
```

---

## 5. Generated Settings Fields

Added to `settings.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Storage
    storage_backend: str = "local"
    storage_local_path: str = "./uploads"
    storage_s3_bucket: str = ""
    storage_s3_region: str = "us-east-1"
    storage_s3_endpoint_url: str = ""
    storage_s3_access_key: str = ""
    storage_s3_secret_key: str = ""
```

---

## 6. `.env.example` Additions

```env
# Storage
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./uploads

# S3 settings (for production or MinIO testing)
STORAGE_S3_BUCKET=my-bucket
STORAGE_S3_REGION=us-east-1
STORAGE_S3_ENDPOINT_URL=http://localhost:9000
STORAGE_S3_ACCESS_KEY=minioadmin
STORAGE_S3_SECRET_KEY=minioadmin
```

---

## 7. CLI Integration Updates

Add to `src/paxx/cli/infra.py` after the "Next steps" section:

```python
# Custom guidance for storage
if name == "storage":
    console.print("\n[bold]Local development:[/bold]")
    console.print("  Files are stored in ./uploads by default")
    console.print("\n[bold]MinIO testing (S3-compatible):[/bold]")
    console.print("  1. Start MinIO: [dim]docker compose up -d minio[/dim]")
    console.print("  2. Open console: [dim]http://localhost:9001[/dim]")
    console.print("  3. Create a bucket in the console")
    console.print("  4. Set env vars:")
    console.print("     [dim]STORAGE_BACKEND=s3[/dim]")
    console.print("     [dim]STORAGE_S3_BUCKET=my-bucket[/dim]")
    console.print("     [dim]STORAGE_S3_ENDPOINT_URL=http://localhost:9000[/dim]")
    console.print("     [dim]STORAGE_S3_ACCESS_KEY=minioadmin[/dim]")
    console.print("     [dim]STORAGE_S3_SECRET_KEY=minioadmin[/dim]")
    console.print("\n[bold]Usage in code:[/bold]")
    console.print("  [dim]from core.storage import get_storage[/dim]")
    console.print("  [dim]storage = get_storage()[/dim]")
    console.print("  [dim]url = await storage.upload('path/file.jpg', data)[/dim]")
```

---

## 8. Usage Examples

### Basic Upload/Download

```python
# features/users/routes.py
from fastapi import UploadFile
from core.storage import get_storage

@router.post("/users/{user_id}/avatar")
async def upload_avatar(user_id: int, file: UploadFile):
    storage = get_storage()

    content = await file.read()
    key = f"avatars/{user_id}/{file.filename}"

    url = await storage.upload(key, content, content_type=file.content_type)

    return {"url": url}


@router.get("/users/{user_id}/avatar")
async def get_avatar(user_id: int, filename: str):
    storage = get_storage()

    key = f"avatars/{user_id}/{filename}"
    content = await storage.download(key)

    return Response(content=content, media_type="image/jpeg")
```

### Presigned URLs (S3 only)

```python
from core.storage import get_storage

@router.get("/files/{file_id}/download-url")
async def get_download_url(file_id: int):
    storage = get_storage()
    key = f"files/{file_id}/document.pdf"

    # Generate a URL valid for 1 hour
    url = await storage.presign(key, expires_in=3600)

    if url is None:
        # Fallback for local backend - serve directly
        return {"url": f"/api/files/{file_id}/download"}

    return {"url": url}
```

### File Validation Helper

```python
# core/storage.py - optional addition

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def validate_image_upload(file: UploadFile) -> bytes:
    """
    Validate an uploaded image file.

    Raises:
        ValueError: If file is invalid
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(f"Invalid file type: {file.content_type}")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {len(content)} bytes")

    return content
```

### Service Layer Integration

```python
# features/documents/services.py
from core.storage import get_storage
from .models import Document

async def create_document(
    db: AsyncSession,
    user_id: int,
    file: UploadFile,
) -> Document:
    storage = get_storage()

    # Upload file
    content = await file.read()
    key = f"documents/{user_id}/{uuid.uuid4()}/{file.filename}"
    url = await storage.upload(key, content, content_type=file.content_type)

    # Create database record
    document = Document(
        user_id=user_id,
        filename=file.filename,
        storage_key=key,
        url=url,
        size=len(content),
        content_type=file.content_type,
    )
    db.add(document)
    await db.commit()

    return document


async def delete_document(db: AsyncSession, document: Document) -> None:
    storage = get_storage()

    # Delete from storage
    await storage.delete(document.storage_key)

    # Delete database record
    await db.delete(document)
    await db.commit()
```

---

## 9. MinIO Setup Guide

### Initial Setup

1. Start MinIO:
   ```bash
   docker compose up -d minio
   ```

2. Access the console at http://localhost:9001
   - Username: `minioadmin`
   - Password: `minioadmin`

3. Create a bucket (e.g., `my-app-uploads`)

4. Update `.env`:
   ```env
   STORAGE_BACKEND=s3
   STORAGE_S3_BUCKET=my-app-uploads
   STORAGE_S3_ENDPOINT_URL=http://localhost:9000
   STORAGE_S3_ACCESS_KEY=minioadmin
   STORAGE_S3_SECRET_KEY=minioadmin
   ```

### Production AWS S3 Setup

1. Create an S3 bucket in AWS Console

2. Create an IAM user with S3 permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject",
           "s3:HeadObject"
         ],
         "Resource": "arn:aws:s3:::my-bucket/*"
       }
     ]
   }
   ```

3. Update environment:
   ```env
   STORAGE_BACKEND=s3
   STORAGE_S3_BUCKET=my-bucket
   STORAGE_S3_REGION=us-east-1
   STORAGE_S3_ACCESS_KEY=AKIA...
   STORAGE_S3_SECRET_KEY=...
   # Leave STORAGE_S3_ENDPOINT_URL empty for AWS S3
   ```

---

## 10. Implementation Checklist

- [ ] Create `src/paxx/infra/storage/__init__.py` (empty)
- [ ] Create `src/paxx/infra/storage/config.py` with InfraConfig
- [ ] Create `src/paxx/infra/storage/dependencies.txt`
- [ ] Create `src/paxx/infra/storage/docker_service.yml`
- [ ] Create `src/paxx/infra/storage/templates/storage.py.jinja`
- [ ] Update `src/paxx/cli/infra.py` with storage-specific guidance
- [ ] Test: `paxx infra add storage` on fresh project
- [ ] Test: Local backend upload/download
- [ ] Test: MinIO backend upload/download
- [ ] Test: Presigned URL generation
- [ ] Test: File deletion

---

## 11. Advanced Patterns

### Streaming Large Files

```python
async def stream_upload(
    storage: StorageBackend,
    key: str,
    file: UploadFile,
    chunk_size: int = 1024 * 1024,  # 1 MB chunks
) -> str:
    """Upload a large file in chunks."""
    from io import BytesIO

    buffer = BytesIO()
    async for chunk in file:
        buffer.write(chunk)

    buffer.seek(0)
    return await storage.upload(key, buffer, content_type=file.content_type)
```

### Multipart Upload (S3)

For very large files (> 100 MB), consider implementing multipart upload:

```python
async def multipart_upload(
    key: str,
    file: UploadFile,
    part_size: int = 10 * 1024 * 1024,  # 10 MB parts
) -> str:
    """Upload a large file using S3 multipart upload."""
    session = aioboto3.Session()

    async with session.client("s3", endpoint_url=endpoint_url) as s3:
        # Create multipart upload
        response = await s3.create_multipart_upload(Bucket=bucket, Key=key)
        upload_id = response["UploadId"]

        parts = []
        part_number = 1

        while True:
            data = await file.read(part_size)
            if not data:
                break

            part = await s3.upload_part(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                PartNumber=part_number,
                Body=data,
            )

            parts.append({"PartNumber": part_number, "ETag": part["ETag"]})
            part_number += 1

        # Complete upload
        await s3.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
```

### Image Processing Pipeline

```python
from PIL import Image
from io import BytesIO

async def upload_with_thumbnail(
    storage: StorageBackend,
    key: str,
    image_data: bytes,
    thumbnail_size: tuple[int, int] = (200, 200),
) -> dict[str, str]:
    """Upload an image and create a thumbnail."""
    # Upload original
    original_url = await storage.upload(key, image_data, content_type="image/jpeg")

    # Create thumbnail
    img = Image.open(BytesIO(image_data))
    img.thumbnail(thumbnail_size)

    thumb_buffer = BytesIO()
    img.save(thumb_buffer, format="JPEG", quality=85)
    thumb_buffer.seek(0)

    # Upload thumbnail
    thumb_key = key.replace(".", "_thumb.")
    thumb_url = await storage.upload(thumb_key, thumb_buffer.read(), content_type="image/jpeg")

    return {"original": original_url, "thumbnail": thumb_url}
```

---

## Summary

The Object Storage implementation provides:

1. **Abstract interface** - `StorageBackend` class with upload, download, delete, exists, presign methods
2. **Local backend** - filesystem-based storage for development with no external dependencies
3. **S3 backend** - production-ready S3-compatible storage using aioboto3
4. **MinIO integration** - Docker service for local S3-compatible testing
5. **Async-first design** - all operations are async, matching Paxx's patterns
6. **Clean configuration** - settings-based backend selection with sensible defaults

This keeps storage concerns isolated in `core/storage.py` while providing flexibility to swap backends without changing application code.
