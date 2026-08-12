"""S3-compatible object storage for local MinIO and Cloudflare R2."""

from datetime import timedelta
from io import BytesIO
from minio.deleteobjects import DeleteObject
from minio.error import S3Error

from minio import Minio

from app.config import (
    MINIO_ACCESS_KEY,
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    MINIO_REGION,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
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
            secure=MINIO_SECURE,
            region=MINIO_REGION,
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
        
    def delete_object(
        self,
        object_name: str,
    ) -> None:

        self.client.remove_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
        )


    def delete_prefix(
        self,
        prefix: str,
    ) -> int:
        """
        Delete every MinIO object under a prefix.

        Example:
            attention-paper/
        """

        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=True,
            )

            object_names = [
                item.object_name
                for item in objects
            ]
        except S3Error as exc:
            if exc.code in {
                "NoSuchBucket",
                "NoSuchKey",
                "NoSuchObject",
                "NotFound",
            }:
                return 0

            raise

        if not object_names:
            return 0

        errors = self.client.remove_objects(
            bucket_name=self.bucket_name,
            delete_object_list=(
                DeleteObject(object_name)
                for object_name in object_names
            ),
        )

        errors_list = list(errors)

        if errors_list:
            first_error = errors_list[0]

            raise RuntimeError(
                f"Failed to delete MinIO object: "
                f"{first_error.object_name}"
            )

        return len(object_names)


    def delete_paper_assets(
        self,
        paper_name: str,
    ) -> int:
        """
        Delete all assets belonging to one paper.
        """

        return self.delete_prefix(
            f"{paper_name}/"
        )
        
    def object_exists(
        self,
        object_name: str,
    ) -> bool:
        """
        Check whether an object exists in the configured bucket.
        """

        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
            )

            return True

        except S3Error as exc:
            if exc.code in {
                "NoSuchKey",
                "NoSuchObject",
                "NoSuchBucket",
                "NotFound",
            }:
                return False

            raise
