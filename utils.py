from pathlib import Path
from urllib.parse import unquote_plus

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
UPLOAD_PREFIX = "uploads/"



def decode_s3_key(key: str) -> str:
    """Decode the URL-encoded key from an S3 event."""
    return unquote_plus(key)



def get_file_extension(key: str) -> str:
    """Return the lowercase suffix for an S3 object key."""
    return Path(key).suffix.lower()



def is_supported_image(key: str) -> bool:
    """Check whether the object key points to a supported image file."""
    return get_file_extension(key) in SUPPORTED_EXTENSIONS


def is_upload_key(key: str) -> bool:
    """Restrict processing to files written under the uploads/ prefix."""
    return key.startswith(UPLOAD_PREFIX)



def get_basename(key: str) -> str:
    """Return the filename stem without the extension."""
    return Path(key).stem



def build_output_key(input_key: str) -> str:
    """Map uploads/<name>.<ext> to outputs/<name>.jpg."""
    return f"outputs/{get_basename(input_key)}.jpg"
