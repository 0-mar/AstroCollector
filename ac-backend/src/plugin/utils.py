import zipfile
from pathlib import Path


def unzip_archive(archive_path: Path, target_directory: Path) -> None:
    # unzip archive
    with zipfile.ZipFile(archive_path, "r") as zip_file:
        zip_file.extractall(target_directory)
