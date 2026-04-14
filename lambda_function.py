import logging
from pathlib import Path

from processor import process_image
from storage import download_file, upload_file
from utils import build_output_key, decode_s3_key, extract_session_id, is_supported_image, is_upload_key

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

INPUT_DIR = Path("/tmp/input")
OUTPUT_DIR = Path("/tmp/output")



def _cleanup_temp_files(input_path: Path, output_path: Path) -> None:
    """Safely delete temporary files from /tmp."""
    if input_path.exists():
        input_path.unlink()
        LOGGER.info("Cleaned up input file: %s", input_path)
    if output_path.exists():
        output_path.unlink()
        LOGGER.info("Cleaned up output file: %s", output_path)


def lambda_handler(event, context):
    """Handle an S3 upload event and write a processed JPEG back to S3.

    Flow:
    1. Parse and validate the S3 event.
    2. Check upload prefix and image format.
    3. Download the source image from S3.
    4. Process the image (convert, compress, resize).
    5. Upload the result back to S3.
    6. Clean up temporary files.
    """
    LOGGER.info("Received Lambda event")

    try:
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        object_key = decode_s3_key(record["s3"]["object"]["key"])
    except (KeyError, IndexError, TypeError) as error:
        LOGGER.exception("Invalid S3 event payload")
        return {"statusCode": 400, "message": "Invalid S3 event payload", "error": str(error)}

    # Extract sessionId for logging and tracing
    session_id = extract_session_id(object_key)
    LOGGER.info("Processing image | bucket=%s | sessionId=%s | key=%s", bucket, session_id or "N/A", object_key)

    if not is_upload_key(object_key):
        message = f"Skipping key outside uploads/ prefix: {object_key}"
        LOGGER.info(message)
        return {"statusCode": 200, "message": message}

    if not is_supported_image(object_key):
        message = f"Skipping unsupported file type: {object_key}"
        LOGGER.warning(message)
        return {"statusCode": 200, "message": message}

    input_path = INPUT_DIR / Path(object_key).name
    output_path = OUTPUT_DIR / f"{Path(object_key).stem}.jpg"
    output_key = build_output_key(object_key)

    try:
        LOGGER.info("Downloading image from S3: s3://%s/%s", bucket, object_key)
        download_file(bucket, object_key, str(input_path))

        LOGGER.info("Processing image: %s", input_path)
        metadata = process_image(str(input_path), str(output_path))

        LOGGER.info("Uploading processed image to S3: s3://%s/%s", bucket, output_key)
        upload_file(bucket, output_key, str(output_path))

        result = {
            "statusCode": 200,
            "bucket": bucket,
            "sessionId": session_id or None,
            "input_key": object_key,
            "output_key": output_key,
            "details": metadata,
        }
        LOGGER.info("Processing complete | output=%s", output_key)
        return result

    except Exception as error:
        LOGGER.exception("Error processing image | sessionId=%s | key=%s", session_id or "N/A", object_key)
        return {
            "statusCode": 500,
            "message": "Failed to process image",
            "error": str(error),
            "sessionId": session_id or None,
        }
    finally:
        LOGGER.info("Cleaning up temporary files")
        _cleanup_temp_files(input_path, output_path)
