"""
Image enrichment.

Responsibilities
----------------
1. Upload extracted images to MinIO.
2. Download images from MinIO.
3. Send images to GPT-4.1 Vision.
4. Store image description and MinIO reference.
"""

import base64

from app.llm.client import OpenAIClient
from app.storage.minio_storage import MinioStorage


class ImageEnricher:

    def __init__(self):

        self.storage = MinioStorage(create_bucket=True)
        self.openai = OpenAIClient().client

    def enrich_chunk(
        self,
        chunk: dict,
    ) -> dict:
        """
        Enrich every image inside a chunk.

        Images are uploaded to MinIO immediately.
        Only the MinIO object reference is retained.
        """

        for index, image in enumerate(
            chunk.get("images", []),
            start=1,
        ):

            base64_image = image.get("base64")

            if not base64_image:
                continue

            # --------------------------------------------------
            # Decode Base64 returned by Unstructured
            # --------------------------------------------------

            image_bytes = base64.b64decode(base64_image)

            mime_type = image.get(
                "mime",
                "image/jpeg",
            )

            extension = mime_type.split("/")[-1]

            # --------------------------------------------------
            # Upload to MinIO
            # --------------------------------------------------

            object_name = self.storage.upload_image_bytes(
                image_bytes=image_bytes,
                paper_name=chunk["paper_name"],
                image_name=f"{chunk['chunk_id']}_figure_{index}.{extension}",
                content_type=mime_type,
            )

            # --------------------------------------------------
            # Store only MinIO reference
            # --------------------------------------------------

            image["storage"] = {
                "provider": "minio",
                "bucket": self.storage.bucket_name,
                "object_name": object_name,
            }

            # --------------------------------------------------
            # Read image back from MinIO
            # (single source of truth)
            # --------------------------------------------------

            image_bytes = self.storage.get_image_bytes(
                object_name
            )

            image_base64 = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            # --------------------------------------------------
            # Generate semantic description
            # --------------------------------------------------

            image["description"] = self.describe_image(
                image_base64=image_base64,
                caption=image.get("caption"),
            )

            # --------------------------------------------------
            # Remove temporary fields
            # --------------------------------------------------

            image.pop("base64", None)
            image.pop("mime", None)

        return chunk

    def describe_image(
        self,
        image_base64: str,
        caption: str | None,
    ) -> str:
        """
        Ask GPT-4.1 Vision to describe the figure.
        """

        prompt = f"""
            You are analysing a figure extracted from a research paper.

            Caption:
            {caption}

            Describe:

            - What the figure represents.
            - Important labels.
            - Overall architecture or flow.
            - Key relationships.
            - Information useful for semantic retrieval.

            Do not hallucinate.

            Return only the description.
        """

        response = self.openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:image/jpeg;base64,{image_base64}"
                                )
                            },
                        },
                    ],
                }
            ],
        )

        return response.choices[0].message.content