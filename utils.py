import secrets
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



def extract_session_id(input_key: str) -> str:
    """Extract sessionId from input key path.
    
    Expected format: uploads/<sessionId>/<filename>.<ext>
    Returns sessionId or empty string if not found.
    """
    parts = input_key.split('/')
    if len(parts) >= 2 and parts[0] == "uploads":
        return parts[1]
    return ""


def _generate_random_suffix() -> str:
    """Generate a 6-character random suffix to prevent filename collisions."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return ''.join(secrets.choice(chars) for _ in range(6))


def build_output_key(input_key: str) -> str:
    """Map uploads/<sessionId>/<filename>.<ext> to outputs/<sessionId>/<filename>-<suffix>.jpg.
    
    Preserves sessionId and adds random suffix to prevent collisions.
    Falls back to flat structure if sessionId is not present.
    """
    session_id = extract_session_id(input_key)
    filename = get_basename(input_key)
    suffix = _generate_random_suffix()
    
    if session_id:
        return f"outputs/{session_id}/{filename}-{suffix}.jpg"
    
    # Fallback: no sessionId in path
    return f"outputs/{filename}-{suffix}.jpg"
