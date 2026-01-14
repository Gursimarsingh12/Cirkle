import os
from core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class ImageUtils:
    MAX_SIZE_BYTES = 3 * 1024 * 1024
    ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]

    @staticmethod
    def validate_image_file(file_path: str, content_type: str) -> None:
        if content_type not in ImageUtils.ALLOWED_TYPES:
            raise ValidationError(
                f"Invalid content type: {content_type}. Allowed: {ImageUtils.ALLOWED_TYPES}"
            )
        if not os.path.exists(file_path):
            raise ValidationError(f"File does not exist: {file_path}")
        if os.path.getsize(file_path) > ImageUtils.MAX_SIZE_BYTES:
            raise ValidationError(
                f"Image size exceeds 3MB limit. Size: {os.path.getsize(file_path)} bytes"
            )

    @staticmethod
    def save_image_file(upload_dir: str, filename: str, file_data: bytes) -> str:
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_data)
        return file_path

    @staticmethod
    def save_user_photo(user_id: str, file_data: bytes, ext: str) -> str:
        folder = os.path.join("user", user_id, "photo")
        os.makedirs(folder, exist_ok=True)
        filename = f"{user_id}_photo.{ext}"
        file_path = os.path.join(folder, filename)
        with open(file_path, "wb") as f:
            f.write(file_data)
        return file_path

    @staticmethod
    def save_user_banner(user_id: str, file_data: bytes, ext: str) -> str:
        folder = os.path.join("user", user_id, "banner")
        os.makedirs(folder, exist_ok=True)
        filename = f"{user_id}_banner.{ext}"
        file_path = os.path.join(folder, filename)
        with open(file_path, "wb") as f:
            f.write(file_data)
        return file_path

    @staticmethod
    def save_tweet_media(
        user_id: str, tweet_id: int, media_index: int, file_data: bytes, ext: str
    ) -> str:
        folder = os.path.join("user", user_id, "tweets", str(tweet_id))
        os.makedirs(folder, exist_ok=True)
        filename = f"{user_id}_{tweet_id}_photo{media_index}.{ext}"
        file_path = os.path.join(folder, filename)
        with open(file_path, "wb") as f:
            f.write(file_data)
        return file_path
