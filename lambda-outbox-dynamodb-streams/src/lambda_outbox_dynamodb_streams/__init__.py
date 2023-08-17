from pathlib import Path

LAMBDA_ZIP_PATH_ARM64 = Path(__file__).parent / "lambda_outbox_dynamodb_streams_arm64.zip"
LAMBDA_ZIP_PATH_X86_64 = Path(__file__).parent / "lambda_outbox_dynamodb_streams_x86_64.zip"

__all__ = [
    "LAMBDA_ZIP_PATH_ARM64",
    "LAMBDA_ZIP_PATH_X86_64",
]
