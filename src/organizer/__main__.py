from pathlib import Path
import shutil
import argparse
import sys
import json
import os
from organizer.logger import log, logger, LOG_FILE
from organizer.exceptions import InvalidFolderError, ProtectedSystemFolder


class FileOrganizerSession:
    def __init__(self, folder_path):
        self.folder = Path(folder_path).resolve()
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
    logger.info(f"Moved: {file.resolve()} to {destination_path.resolve()}")


def get_user_config_dir():
    """Return the user config directory path (platform-specific)."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "organizer"
    # Linux/macOS and fallback
    return Path.home() / ".config" / "organizer"


def ensure_user_config():
    """Create user config directory and copy default extensions.json if missing."""
    user_config_dir = get_user_config_dir()
    user_config_file = user_config_dir / "extensions.json"

    user_config_dir.mkdir(parents=True, exist_ok=True)

    if not user_config_file.exists():
        default_config = Path(__file__).parent / "config" / "extensions.json"
        if default_config.exists():
            shutil.copy(default_config, user_config_file)
            print(f"Created user config file: {user_config_file}")
            print("")
        else:
            # fallback minimal config (should not happen normally)
            fallback = {
                "Images": [".jpg", ".jpeg", ".png", ".gif"],
                "Documents": [".pdf", ".txt"],
                "Others": [],
            }
            with open(user_config_file, "w") as f:
                json.dump(fallback, f, indent=2)
            print(
                f"Default config missing. Created minimal config at: {user_config_file}"
            )
            print("")
    else:

        print(f"Using user config: {user_config_file}")
        print("")

    return user_config_file


@log
def sortFiles(folder, session, dry_run=False):

    config_path = ensure_user_config()

    with open(config_path, "r") as f:
        extensions = json.load(f)

    mapping = {}
    for category, exts in extensions.items():
        for ext in exts:
            mapping[ext.lower()] = category

    current_script = Path(__file__).resolve()

    # Exclude project root
    project_root = current_script.parent.parent

    for file in folder.iterdir():

        abs_file = file.resolve()

        if not file.is_file():
            continue

        if abs_file == current_script or abs_file == LOG_FILE.resolve():
            continue

        if file.name.startswith("."):
            continue

        file_extension = file.suffix.lower()
        category = mapping.get(file_extension, "Others")
        moveFiles(file, folder, category, dry_run=dry_run)
        if not dry_run:
            session.count += 1


def stream_log_lines(log_path):
    with open(log_path, "r") as f:
        for line in f:
            yield line.strip()


def get_moves_from_log(lines):
    for line in lines:

        if "Moved:" in line and " to " in line:
            try:
                parts = line.split("Moved: ")[1].split(" to ")
                original_path = parts[0].strip()
                new_path = parts[1].strip()

                yield {"original": original_path, "current": new_path}
            except IndexError:
                continue


def run_undo(log_path, number_of_moves):
    lines = stream_log_lines(log_path)
    all_moves = list(get_moves_from_log(lines))

    if not all_moves:
        print("No moves found to undo.")
        return

    to_undo = all_moves[-number_of_moves:]
    print(f"Undoing the last {len(to_undo)} moves...")

    for move in reversed(to_undo):
        current = Path(move["current"])
        original = Path(move["original"])

        if current.exists():
            try:
                shutil.move(str(current), str(original))
                print(f"Restored: {original.name}")
            except Exception as e:
                print(f"Error restoring {original.name}: {e}")
        else:
            print(f"Skip: {current} not found.")


def main():
    parser = argparse.ArgumentParser(
        prog="organize",
        usage="organize <folder>",
        description="Organize files in a folder by type (Images, Videos, Documents, etc.)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  organize C:\\Users\\name\\Downloads # organize the Downloads Folders
  organize "C:\\Users\\name\\Downloads" --dry-run # preview the changes
  organize .          # organize current directory
  organize -u 5 # undo the last 5 moves 
""",
    )

    parser.add_argument(
        "folder",
        nargs="?",
        help="path to folder to organize (use '.' for current directory)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="preview the changes without committing them (optional)",
    )

    parser.add_argument(
        "-u",
        "--undo",
        nargs="?",
        const=10,
        type=int,
        metavar="N",
        help="undo the last N changes based on the log file (default: 10)",
    )

    args = parser.parse_args()

    if args.undo:
        run_undo(LOG_FILE, args.undo)
        return
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
            logger.info(f"---STARTING SESSION FOR {folder_path}---")
            sortFiles(session.folder, session, dry_run=args.dry_run)
            print("")
            print(f"Saved logs to: {LOG_FILE}")
    except ProtectedSystemFolder as e:
        print(f"SECURITY ALERT: {e}")
        logger.critical(f"SECURITY VIOLATION ATTEMPT: {e.foldername}")
    except InvalidFolderError as e:
        print(f"PATH ERROR: {e}")
        logger.critical(f"INVALID PATH:  {e.foldername}")
    except Exception as e:
        print(f"UNCAPTURED ERROR: {e}")

    finally:
        logger.info(f"---ENDING SESSION FOR {folder_path}---")


if __name__ == "__main__":
    main()
