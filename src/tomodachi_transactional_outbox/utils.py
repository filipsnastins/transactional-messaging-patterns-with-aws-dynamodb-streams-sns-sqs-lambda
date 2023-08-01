import io
import os
import zipfile
from pathlib import Path


def create_in_memory_zip(dir_path: Path) -> io.BytesIO:
    in_memory_zip = io.BytesIO()
    with zipfile.ZipFile(in_memory_zip, "w", zipfile.ZIP_DEFLATED) as f:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = Path(root) / file
                rel_path = Path(file_path).relative_to(dir_path)
                f.write(file_path, arcname=rel_path)
    in_memory_zip.seek(0)
    return in_memory_zip
