from pathlib import Path
import shutil
import os
from logger import log, logger
from exceptions import InvalidFolderError, ProtectedSystemFolder
from extensions import config


class FileOrganizerSession:
    def __init__(self, folder_path):
        self.folder = Path(folder_path)
        self.count = 0
        self.protected_folders = {
            "Windows",
            "System32",
            "SysWOW64",
            "Program Files",
            "Program Files (x86)",
            "ProgramData",
            "$Recycle.Bin",
            "System Volume Information",
            "Boot",
            "Recovery",
            "MSOCache",
        }

    def __enter__(self):
        if not self.folder.exists():
            logger.critical(f"{self.folder} does not exist.")
            raise InvalidFolderError("The folder does not exist.", self.folder)

        if self.folder.name.lower() in self.protected_folders:
            logger.critical(f"{self.folder} is a protected system folder.")
            raise ProtectedSystemFolder(
                "Access Denied: Protected system folder.", self.folder
            )

        print(f"--- Starting session for [{self.folder}] ---")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"Session failed: {exc_val}")
            logger.error(f"Error: {exc_val}")
        print(f"--- Session Finished. Files moved: {self.count} ---")
        return False


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
    logger.info(f"Moved: {file.name} to {destination_path}")


@log
def sortFiles(folder, session):
    for file in folder.iterdir():
        if not file.is_file():
            continue
        file_extension = file.suffix
        category = config.extensions.get(file_extension, "Others")
        moveFiles(file, folder, category)
        session.count += 1


if __name__ == "__main__":
    try:
        with FileOrganizerSession("test_folder") as session:
            sortFiles(session.folder, session)

    except ProtectedSystemFolder as e:
        print(f"SECURITY ALERT: {e}")
        logger.critical(f"Security violation attempt on {e.foldername}")

    except InvalidFolderError as e:
        print(f"PATH ERROR: {e}")

    except Exception as e:
        print(f"UNCAPTURED ERROR: {e}")
