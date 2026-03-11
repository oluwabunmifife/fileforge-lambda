import logging
from pathlib import Path

from processor import process_image
from storage import download_file, upload_file
from utils import build_output_key, decode_s3_key, is_supported_image, is_upload_key

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

INPUT_DIR = Path("/tmp/input")
OUTPUT_DIR = Path("/tmp/output")



def lambda_handler(event, context):
    """Handle an S3 upload event and write a processed JPEG back to S3.

    Flow:
    1. Read the first S3 record from the Lambda event.
    2. Download the uploaded object into /tmp/input.
    3. Convert/compress/resize the image into /tmp/output.
    4. Upload the final JPEG to the outputs/ prefix in the same bucket.
    """
    LOGGER.info("Received event: %s", event)

    try:
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        object_key = decode_s3_key(record["s3"]["object"]["key"])
    except (KeyError, IndexError, TypeError) as error:
        LOGGER.exception("Invalid S3 event payload")
        return {"statusCode": 400, "message": "Invalid S3 event payload", "error": str(error)}

    if not is_upload_key(object_key):
        message = f"Skipping key outside uploads/ prefix: {object_key}"
        LOGGER.info(message)
        return {"statusCode": 200, "message": message}

    if not is_supported_image(object_key):
        message = f"Skipping unsupported file type for key: {object_key}"
        LOGGER.warning(message)
        return {"statusCode": 200, "message": message}

    input_path = INPUT_DIR / Path(object_key).name
    output_path = OUTPUT_DIR / f"{Path(object_key).stem}.jpg"
    output_key = build_output_key(object_key)

    LOGGER.info("Starting processing for s3://%s/%s", bucket, object_key)
    download_file(bucket, object_key, str(input_path))

    metadata = process_image(str(input_path), str(output_path))
    upload_file(bucket, output_key, str(output_path))

    result = {
        "statusCode": 200,
        "bucket": bucket,
        "input_key": object_key,
        "output_key": output_key,
        "details": metadata,
    }
    LOGGER.info("Processing complete: %s", result)
    return result
