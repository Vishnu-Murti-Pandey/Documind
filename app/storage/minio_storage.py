"""
MinIO Storage Client.

Responsible for interacting with MinIO object storage.
"""

from datetime import timedelta
from io import BytesIO

from minio import Minio

from app.config import (
    MINIO_ACCESS_KEY,
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
)


class MinioStorage:

    def __init__(
        self,
        create_bucket: bool = False,
    ) -> None:

        self.bucket_name = MINIO_BUCKET

        self.client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )

        if create_bucket:
            self.ensure_bucket_exists()

    def ensure_bucket_exists(
        self,
    ) -> None:
        """
        Create the configured bucket if it does not exist.

        Use this during ingestion or explicit initialization,
        not when serving normal asset requests.
        """

        if not self.client.bucket_exists(
            self.bucket_name
        ):
            self.client.make_bucket(
                self.bucket_name
            )

    def upload_image_bytes(
        self,
        image_bytes: bytes,
        paper_name: str,
        image_name: str,
        content_type: str,
    ) -> str:

        self.ensure_bucket_exists()

        object_name = (
            f"{paper_name}/images/{image_name}"
        )

        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=BytesIO(image_bytes),
            length=len(image_bytes),
            content_type=content_type,
        )

        return object_name

    def get_image_bytes(
        self,
        object_name: str,
    ) -> bytes:

        response = self.client.get_object(
            self.bucket_name,
            object_name,
        )

        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def get_presigned_url(
        self,
        object_name: str,
        expires_minutes: int = 15,
    ) -> str:

        return self.client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            expires=timedelta(
                minutes=expires_minutes
            ),
        )