import io
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def package_lambda_as_zip(lambda_path: Path) -> io.BytesIO:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        shutil.copytree(lambda_path, tmp_dir_path, dirs_exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--target", "."],
            cwd=tmp_dir_path,
        )
        return zip_directory(tmp_dir_path)


def zip_directory(dir_path: Path) -> io.BytesIO:
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as f:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = Path(root) / file
                rel_path = Path(file_path).relative_to(dir_path)
                f.write(file_path, arcname=rel_path)
    data.seek(0)
    return data
