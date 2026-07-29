"""
MinIO Storage Client.

Responsible for uploading and downloading assets.

The rest of the application should never directly
interact with MinIO.
"""

from io import BytesIO

from minio import Minio

from app.config import (
    MINIO_ACCESS_KEY,
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
)


class MinioStorage:

    def __init__(self):

        self.bucket_name = MINIO_BUCKET

        self.client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )

        self._create_bucket()

    def _create_bucket(self):

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

        data = response.read()

        response.close()
        response.release_conn()

        return data