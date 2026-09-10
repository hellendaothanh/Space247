"""Private KYC storage and short-lived retrieval grants."""
from __future__ import annotations
import asyncio
import shutil
from datetime import timedelta
from pathlib import Path
from tempfile import SpooledTemporaryFile
from uuid import UUID, uuid4
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from src.core.config import settings
from src.core.security import create_access_token

ALLOWED_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_IMAGE_PIXELS = 25_000_000

class KycStorage:
    def _backend(self) -> str:
        backend = settings.KYC_STORAGE_BACKEND.lower()
        if backend not in {"local", "s3"}:
            raise RuntimeError("KYC_STORAGE_BACKEND must be local or s3")
        if backend == "s3" and not all((settings.KYC_S3_BUCKET, settings.KYC_S3_ACCESS_KEY_ID, settings.KYC_S3_SECRET_ACCESS_KEY)):
            raise RuntimeError("S3/R2 KYC storage is not configured")
        return backend

    def _validate(self, upload: UploadFile, data: SpooledTemporaryFile) -> str:
        extension = ALLOWED_CONTENT_TYPES.get(upload.content_type or "")
        if not extension:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="KYC documents must be JPEG, PNG, or WebP images within the size limit")
        try:
            data.seek(0)
            with Image.open(data) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"} or image.width * image.height > MAX_IMAGE_PIXELS:
                    raise ValueError("unsafe image")
                image.verify()
            data.seek(0)
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="KYC document is not a safe, valid image") from exc
        return extension

    async def store(self, user_id: UUID, side: str, upload: UploadFile) -> tuple[str, str]:
        if side not in {"front", "back"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="KYC document side must be front or back")
        backend = self._backend()
        data = SpooledTemporaryFile(max_size=min(settings.KYC_MAX_FILE_SIZE_BYTES, 1024 * 1024), mode="w+b")
        try:
            total = 0
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > settings.KYC_MAX_FILE_SIZE_BYTES:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="KYC document exceeds the size limit")
                data.write(chunk)
            extension = self._validate(upload, data)
            key = f"{user_id}/{side}/{uuid4().hex}{extension}"
            if backend == "local":
                path = Path(settings.KYC_LOCAL_STORAGE_PATH) / key
                def write_local() -> None:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    data.seek(0)
                    with path.open("wb") as destination:
                        shutil.copyfileobj(data, destination)
                await asyncio.to_thread(write_local)
                return key, upload.content_type or "image/jpeg"
            import boto3
            client = boto3.client("s3", endpoint_url=settings.KYC_S3_ENDPOINT_URL or None, aws_access_key_id=settings.KYC_S3_ACCESS_KEY_ID, aws_secret_access_key=settings.KYC_S3_SECRET_ACCESS_KEY, region_name=settings.KYC_S3_REGION)
            data.seek(0)
            await asyncio.to_thread(client.put_object, Bucket=settings.KYC_S3_BUCKET, Key=key, Body=data, ContentType=upload.content_type, CacheControl="private, no-store")
            return key, upload.content_type or "image/jpeg"
        finally:
            data.close()

    async def delete(self, key: str) -> None:
        if self._backend() == "s3":
            import boto3
            client = boto3.client("s3", endpoint_url=settings.KYC_S3_ENDPOINT_URL or None, aws_access_key_id=settings.KYC_S3_ACCESS_KEY_ID, aws_secret_access_key=settings.KYC_S3_SECRET_ACCESS_KEY, region_name=settings.KYC_S3_REGION)
            await asyncio.to_thread(client.delete_object, Bucket=settings.KYC_S3_BUCKET, Key=key)
            return
        path = (Path(settings.KYC_LOCAL_STORAGE_PATH) / key).resolve()
        root = Path(settings.KYC_LOCAL_STORAGE_PATH).resolve()
        if path.is_relative_to(root) and path.is_file(): path.unlink()

    async def grant(self, key: str, content_type: str) -> str:
        if self._backend() == "s3":
            import boto3
            client = boto3.client("s3", endpoint_url=settings.KYC_S3_ENDPOINT_URL or None, aws_access_key_id=settings.KYC_S3_ACCESS_KEY_ID, aws_secret_access_key=settings.KYC_S3_SECRET_ACCESS_KEY, region_name=settings.KYC_S3_REGION)
            return await asyncio.to_thread(client.generate_presigned_url, "get_object", Params={"Bucket": settings.KYC_S3_BUCKET, "Key": key, "ResponseCacheControl": "private, no-store"}, ExpiresIn=settings.KYC_RETRIEVAL_TTL_SECONDS)
        token = create_access_token(key, extra_claims={"scope": "kyc:read", "content_type": content_type}, expires_delta=timedelta(seconds=settings.KYC_RETRIEVAL_TTL_SECONDS))
        return f"/api/v1/kyc/documents/stream?grant={token}"

    def local_path(self, key: str) -> Path:
        root = Path(settings.KYC_LOCAL_STORAGE_PATH).resolve(); path = (root / key).resolve()
        if not path.is_relative_to(root): raise HTTPException(status_code=404, detail="Document not found")
        return path

kyc_storage = KycStorage()
