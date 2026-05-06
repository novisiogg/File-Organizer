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
            logger.info(
                f"Successfully created user config file at: {user_config_file} "
            )
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
            logger.info(f"Created minimal config at: {user_config_file}")
            print("")
    else:

        print(f"Using user config: {user_config_file}")
        print("")

    return user_config_file


@log
def sortFiles(folder, session, dry_run=False, recursive=False):
    config_path = ensure_user_config()
    with open(config_path, "r") as f:
        extensions = json.load(f)

    mapping = {ext.lower(): cat for cat, exts in extensions.items() for ext in exts}
    current_script = Path(__file__).resolve()

    files_to_process = folder.rglob("*") if recursive else folder.iterdir()

    for file in files_to_process:
        abs_file = file.resolve()

        if not file.is_file():
            continue

        if abs_file == current_script or abs_file == LOG_FILE.resolve():
            continue

        if any(part.startswith(".") for part in file.parts):
            continue

        if recursive:
            if (
                any(cat in file.parts for cat in extensions.keys())
                or "Others" in file.parts
            ):
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


def get_moves_from_log(lines, target_folder):
    target_str = f"--- STARTING SESSION FOR {target_folder} ---"
    in_session = False
    session_moves = []

    for line in lines:
        if target_str in line:
            in_session = True
            session_moves = []
            continue

        if f"--- ENDING SESSION FOR {target_folder} ---" in line:
            in_session = False
            continue

        if in_session and "Moved:" in line and " to " in line:
            try:
                parts = line.split("Moved: ")[1].split(" to ")
                session_moves.append(
                    {"original": parts[0].strip(), "current": parts[1].strip()}
                )
            except IndexError:
                continue

    for move in session_moves:
        yield move


def run_undo(log_path, target_folder, limit=10):
    lines = stream_log_lines(log_path)
    moves = list(get_moves_from_log(lines, target_folder))

    if not moves:
        print(f"No recent session found for: {target_folder}")
        return

    to_undo = moves[-limit:]
    print(f"Reversing {len(to_undo)} moves for {target_folder}...")
    print("")
    for move in reversed(to_undo):
        current = Path(move["current"])
        original = Path(move["original"])
        if current.exists():
            try:
                shutil.move(str(current), str(original))
                print(f"Restored: {original.name}")
                logger.info(f"UNDO: Restored {original}")
            except Exception as e:
                print(f"Couldn't restore {original.name}: {e}")
                logger.error(
                    f"UNDO ERROR: Could not move {current} back to {original}. Reason: {e}"
                )
        else:
            print(f"Skip: {current.name} (not found)")
            logger.warning(
                f"UNDO SKIP: Source file {current} disappeared before restore."
            )


def main():
    parser = argparse.ArgumentParser(
        prog="organize",
        usage="organize <folder>",
        description="Organize files in a folder by type (Images, Videos, Documents, etc.)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  `organize C:\\Users\\name\\Downloads`
      Organize Downloads folder
      
  `organize \"C:\\Users\\name\\Downloads\" --dry-run`
      Preview changes without moving
      
  `organize . -r`
      Organize current directory and all subdirectories
      
  `organize C:\\Users\\name\\Downloads -u 5`
      Undo the last 5 moves
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

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="organize subdirectories as well (default: False)",
    )
    args = parser.parse_args()

    if args.folder is None:
        parser.print_help()
        sys.exit(0)

    folder_path = Path(args.folder).resolve()

    if args.undo:
        num = args.undo if isinstance(args.undo, int) else 10
        run_undo(LOG_FILE, folder_path, num)
        return

    try:
        with FileOrganizerSession(folder_path) as session:
            print(f"Organizing folder: {folder_path}")
            logger.info(f"--- STARTING SESSION FOR {folder_path} ---")
            sortFiles(
                session.folder, session, dry_run=args.dry_run, recursive=args.recursive
            )
            print("")

    except ProtectedSystemFolder as e:
        print(f"SECURITY ALERT: {e}")
        logger.critical(f"SECURITY VIOLATION ATTEMPT: {e.foldername}")

    except InvalidFolderError as e:
        print(f"PATH ERROR: {e}")
        logger.critical(f"INVALID PATH:  {e.foldername}")

    except Exception as e:
        print(f"UNCAPTURED ERROR: {e}")

    finally:
        if "folder_path" in locals():
            logger.info(f"--- ENDING SESSION FOR {folder_path} ---")

        # Get the path to the config file
        config_file = get_user_config_dir() / "extensions.json"

        print(f"Config file used: {config_file}")
        print(f"Saved logs to: {LOG_FILE}")


if __name__ == "__main__":
    main()
