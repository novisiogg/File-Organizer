import os
from pathlib import Path
import shutil
from logging import Logger

extensions = {
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".apng": "Images",
    ".avif": "Images",
    ".jfif": "Images",
    ".pjpeg": "Images",
    ".pjp": "Images",
    ".gif": "Images",
    ".svg": "Images",
    ".webp": "Images",
    ".bmp": "Images",
    ".tiff": "Images",
    ".ico": "Images",
    ".mp4": "Videos",
    ".mov": "Videos",
    ".webm": "Videos",
    ".mkv": "Videos",
    ".flv": "Videos",
    ".vob": "Videos",
    ".ogv": "Videos",
    ".avi": "Videos",
    ".wmv": "Videos",
    ".m4v": "Videos",
    ".mpg": "Videos",
    ".mpeg": "Videos",
    ".3gp": "Videos",
    ".3g2": "Videos",
    ".f4v": "Videos",
    ".pdf": "Documents",
    ".txt": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".odt": "Documents",
    ".rtf": "Documents",
    ".epub": "Documents",
    ".md": "Documents",
    ".ppt": "Documents",
    ".pptx": "Documents",
    ".xls": "Documents",
    ".xlsx": "Documents",
    ".csv": "Documents",
    ".mp3": "Audio",
    ".wav": "Audio",
    ".aac": "Audio",
    ".flac": "Audio",
    ".ogg": "Audio",
    ".m4a": "Audio",
    ".wma": "Audio",
    ".aiff": "Audio",
    ".alac": "Audio",
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    ".bz2": "Archives",
    ".json": "Data",
    ".xml": "Data",
    ".yml": "Data",
    ".yaml": "Data",
    ".sql": "Data",
    ".log": "Data",
}


def getSuffix(file):
    suffix = Path(file).suffix
    return suffix


def moveFiles(file, folder, category):
    destination_folder = folder / category
    destination_folder.mkdir(exist_ok=True)

    destination_path = destination_folder / file.name

    if destination_path.exists():
        print(f"{file.name} already exists in {destination_folder}")

        stem = file.stem
        suffix = file.suffix

        count = 1
        while True:
            new_name = f"{stem}({count}){suffix}"
            new_path = destination_folder / new_name

            if not new_path.exists():
                destination_path = new_path
                break

            count += 1

    shutil.move(str(file), str(destination_path))
    print(f"Moved: {file.name} → {destination_path}")


def sortFiles(folder):
    for file in folder.iterdir():
        if not file.is_file():
            continue
        file_extension = getSuffix(file).lower()

        category = extensions.get(file_extension, "Others")
        moveFiles(file, folder, category)


if __name__ == "__main__":
    sortFiles(Path("test_folder"))
