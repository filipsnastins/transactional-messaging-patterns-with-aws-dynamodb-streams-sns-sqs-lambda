import io
import os
import zipfile
from pathlib import Path


def create_in_memory_zip(dir_path: Path) -> io.BytesIO:
    in_memory_zip = io.BytesIO()  # Create an in-memory buffer to hold the ZIP data

    with zipfile.ZipFile(in_memory_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate the relative path inside the ZIP archive
                rel_path = os.path.relpath(file_path, dir_path)
                zipf.write(file_path, arcname=rel_path)

    in_memory_zip.seek(0)  # Move the file pointer to the beginning of the buffer
    return in_memory_zip
