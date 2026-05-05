from pathlib import Path
import shutil
import argparse
import sys
import json
from organizer.logger import log, logger
from organizer.exceptions import InvalidFolderError, ProtectedSystemFolder


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
        self.isRunning = True

    def __enter__(self):
        if not self.folder.exists():
            logger.critical(f"{self.folder} does not exist.")
            logger.critical(
                f"Attempt to move a folder that does not exist: {self.folder.name}"
            )
            raise InvalidFolderError("The folder does not exist", self.folder)

        if self.folder.name.lower() in self.protected_folders:
            logger.critical(
                f"Attempt to move system protected folder: {self.folder.name}"
            )
            raise ProtectedSystemFolder(
                "Access Denied: Protected system folder.", self.folder
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"Session failed: {exc_val}")
            logger.error(f"Error: {exc_val}")
        print(f"Files moved: {self.count}")
        return False


def moveFiles(file, folder, category, dry_run=False):
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
    if dry_run:
        print(f"[DRY RUN] Would move: {file.name} → {destination_path}")
        return

    shutil.move(str(file), str(destination_path))
    print(f"Moved: {file.name} → {destination_path}")
    logger.info(f"Moved: {file.name} to {destination_path}")


@log
def sortFiles(folder, session, dry_run=False):

    config_path = Path(__file__).parent / "config" / "extensions.json"

    with open(config_path, "r") as f:
        extensions = json.load(f)

    mapping = {}
    for category, exts in extensions.items():
        for ext in exts:
            mapping[ext] = category

    for file in folder.iterdir():
        if not file.is_file():
            continue

        if file.name.startswith("."):
            continue

        file_extension = file.suffix.lower()
        category = mapping.get(file_extension, "Others")
        if dry_run:
            print(f"[DRY RUN]: {file.name} -> {category}")

        else:
            moveFiles(file, folder, category, dry_run=dry_run)
            session.count += 1


def main():
    parser = argparse.ArgumentParser(
        prog="organize",
        usage="organize <folder>",
        description="Organize files in a folder by type (Images, Videos, Documents, etc.)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  organize C:\\Users\\name\\Downloads
  organize "C:\\Users\\name\\Downloads" --dry-run
  organize .          # organize current directory
""",
    )

    parser.add_argument(
        "folder",
        nargs="?",
        help="path to folder to organize (use '.' for current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="preview the changes without committing them. (optional)",
    )

    args = parser.parse_args()
    if args.folder is None:
        parser.print_help()
        sys.exit(0)

    if args.folder == ".":
        folder_path = Path.cwd().resolve()
    else:
        folder_path = Path(args.folder).resolve()

    try:
        with FileOrganizerSession(folder_path) as session:
            print(f"Organizing folder: {folder_path}")
            print("")
            sortFiles(session.folder, session, dry_run=args.dry_run)

    except ProtectedSystemFolder as e:
        print(f"SECURITY ALERT: {e}")
        logger.critical(f"SECURITY VIOLATION ATTEMPT: {e.foldername}")

    except InvalidFolderError as e:
        print(f"PATH ERROR: {e}")
        logger.critical(f"INVALID PATH:  {e.foldername}")

    except Exception as e:
        print(f"UNCAPTURED ERROR: {e}")


if __name__ == "__main__":
    main()
