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
        logger.info(f"Initialized session for folder: {self.folder}")

    def __enter__(self):
        if not self.folder.exists():
            logger.critical(f"{self.folder} does not exist.")
            logger.critical(
                f"Attempt to access a folder that does not exist: {self.folder.name}"
            )
            raise InvalidFolderError("The folder does not exist", self.folder)

        if any(self.folder.name.lower() == pf.lower() for pf in self.protected_folders):
            logger.critical(
                f"Attempt to organize system protected folder: {self.folder.name}"
            )
            raise ProtectedSystemFolder(
                "Access Denied: Protected system folder.", self.folder
            )

        logger.info(f"Session validation passed for: {self.folder}")
        logger.info("")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"Session failed: {exc_val}")
            logger.error(f"Session failed with error: {exc_val}", exc_info=True)
        else:
            logger.info(f"Session completed successfully. Files moved: {self.count}")

        print(f"Files moved: {self.count}")
        return False


def moveFiles(file, folder, category, dry_run=False):
    destination_folder = folder / category

    if not dry_run:
        try:
            destination_folder.mkdir(exist_ok=True)
            logger.info(f"Created folder: {destination_folder}")
            logger.debug(f"Ensured destination folder exists: {destination_folder}")
        except Exception as e:
            logger.error(
                f"Failed to create destination folder {destination_folder}: {e}"
            )
            raise

    destination_path = destination_folder / file.name

    if destination_path.exists():
        print(f"{file.name} already exists in {destination_folder}")
        logger.info(f"File collision detected: {file.name} in {destination_folder}")

        stem = file.stem
        suffix = file.suffix

        count = 1
        while True:
            new_name = f"{stem}({count}){suffix}"
            new_path = destination_folder / new_name

            if not new_path.exists():
                destination_path = new_path
                logger.info(
                    f"Collision resolved: Renaming {file.name} to {new_path.name}"
                )
                break

            count += 1

    if dry_run:
        print(f"[DRY RUN] Would move: {file.name} → {destination_path}")
        logger.info(f"[DRY RUN] Would move: {file.resolve()} → {destination_path}")
        return

    try:
        shutil.move(str(file), str(destination_path))
        print(f"Moved: {file.name} → {destination_path}")
        logger.info(f"Moved: {file.resolve()} to {destination_path.resolve()}")
    except Exception as e:
        logger.error(f"Failed to move {file.name} to {destination_path}: {e}")
        raise


def get_user_config_dir():
    """Return the user config directory path (platform-specific)."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            config_dir = Path(appdata) / "organizer"
            logger.debug(f"Windows config directory: {config_dir}")
            return config_dir
    # Linux/macOS and fallback
    config_dir = Path.home() / ".config" / "organizer"
    logger.debug(f"Unix-like config directory: {config_dir}")
    return config_dir


def ensure_user_config():
    """Create user config directory and copy default extensions.json if missing."""
    user_config_dir = get_user_config_dir()
    user_config_file = user_config_dir / "extensions.json"

    try:
        user_config_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created folder: {user_config_dir}")
        logger.info(f"Ensured config directory exists: {user_config_dir}")
    except Exception as e:
        logger.error(f"Failed to create config directory {user_config_dir}: {e}")
        raise

    if not user_config_file.exists():
        default_config = Path(__file__).parent / "config" / "extensions.json"
        if default_config.exists():
            try:
                shutil.copy(default_config, user_config_file)
                print(f"Created user config file: {user_config_file}")
                logger.info(
                    f"Successfully created user config file at: {user_config_file}"
                )
                print("")
            except Exception as e:
                logger.error(f"Failed to copy default config: {e}")
                raise
        else:
            # fallback minimal config (should not happen normally)
            logger.warning("Default config missing, creating minimal fallback config")
            fallback = {
                "Images": [".jpg", ".jpeg", ".png", ".gif"],
                "Documents": [".pdf", ".txt"],
                "Others": [],
            }
            try:
                with open(user_config_file, "w") as f:
                    json.dump(fallback, f, indent=2)
                print(
                    f"Default config missing. Created minimal config at: {user_config_file}"
                )
                logger.info(f"Created minimal config at: {user_config_file}")
                print("")
            except Exception as e:
                logger.error(f"Failed to create minimal config: {e}")
                raise
    else:
        logger.info(f"Using existing config file: {user_config_file}")

    return user_config_file


@log
def sortFiles(folder, session, dry_run=False, recursive=False):
    logger.info(f"Starting sortFiles - Recursive: {recursive}, Dry run: {dry_run}")

    config_path = ensure_user_config()
    try:
        with open(config_path, "r") as f:
            extensions = json.load(f)
        logger.info(f"Loaded extensions config from: {config_path}")
        logger.debug(f"Extension categories: {list(extensions.keys())}")
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        raise

    mapping = {ext.lower(): cat for cat, exts in extensions.items() for ext in exts}
    current_script = Path(__file__).resolve()

    files_to_process = folder.rglob("*") if recursive else folder.iterdir()
    processed_count = 0
    skipped_count = 0

    for file in files_to_process:
        abs_file = file.resolve()

        if not file.is_file():
            logger.debug(f"Skipped directory: {file}")
            continue

        if abs_file == current_script or abs_file == LOG_FILE.resolve():
            logger.debug(f"Skipped protected file: {file.name}")
            skipped_count += 1
            continue

        if any(part.startswith(".") for part in file.parts):
            logger.debug(f"Skipped hidden file: {file}")
            skipped_count += 1
            continue

        if recursive:
            if (
                any(cat in file.parts for cat in extensions.keys())
                or "Others" in file.parts
            ):
                logger.debug(f"Skipped already categorized file: {file}")
                skipped_count += 1
                continue

        file_extension = file.suffix.lower()
        category = mapping.get(file_extension, "Others")

        logger.debug(
            f"Processing {file.name} - Extension: {file_extension}, Category: {category}"
        )

        try:
            moveFiles(file, folder, category, dry_run=dry_run)
            processed_count += 1

            if not dry_run:
                session.count += 1
        except Exception as e:
            logger.error(f"Error processing file {file.name}: {e}")
            continue

    logger.info(
        f"Completed sortFiles - Processed: {processed_count}, Skipped: {skipped_count}"
    )


def stream_log_lines(log_path):
    """Generator to stream log file lines."""
    try:
        with open(log_path, "r") as f:
            for line in f:
                yield line.strip()
    except FileNotFoundError:
        logger.error(f"Log file not found: {log_path}")
        return
    except Exception as e:
        logger.error(f"Error reading log file {log_path}: {e}")
        return


def get_moves_from_log(lines, target_folder):
    """Extract move operations from log lines for a specific folder."""
    target_str = f"--- STARTING SESSION FOR {Path(target_folder).resolve()} ---"
    in_session = False
    session_moves = []

    for line in lines:
        if target_str in line:
            in_session = True
            session_moves = []
            logger.debug(f"Found session start marker for {target_folder}")
            continue

        if f"--- ENDING SESSION FOR {target_folder} ---" in line:
            in_session = False
            logger.debug(f"Found session end marker for {target_folder}")
            continue

        if in_session and "Moved:" in line and " to " in line:
            try:
                parts = line.split("Moved: ")[1].split(" to ")
                session_moves.append(
                    {"original": parts[0].strip(), "current": parts[1].strip()}
                )
            except IndexError:
                logger.warning(f"Failed to parse move line: {line}")
                continue

    logger.info(f"Extracted {len(session_moves)} moves from log for {target_folder}")
    for move in session_moves:
        yield move


def run_undo(log_path, target_folder, extensions, limit=10):
    """Undo the last N file moves for a specific folder."""
    logger.info(f"Starting undo operation - Folder: {target_folder}, Limit: {limit}")

    if not log_path.exists():
        print(f"Log file not found: {log_path}")
        logger.error(f"Cannot undo: Log file not found at {log_path}")
        return

    lines = stream_log_lines(log_path)
    moves = list(get_moves_from_log(lines, target_folder))

    if not moves:
        print(f"No recent session found for: {target_folder}")
        logger.warning(f"No session found in log for: {target_folder}")
        return

    to_undo = moves[-limit:]
    print(f"Reversing {len(to_undo)} moves for {target_folder}...")
    print("")
    logger.info(f"Reversing {len(to_undo)} moves")

    success_count = 0
    error_count = 0

    for move in reversed(to_undo):
        current = Path(move["current"])
        original = Path(move["original"])

        if current.exists():
            try:
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(current), str(original))
                print(f"Restored: {original.name}")
                logger.info(f"Restored: {current} → {original}")
                success_count += 1
            except Exception as e:
                print(f"Error restoring {original.name}: {e}")
                logger.error(f"Failed to restore {current} to {original}: {e}")
                error_count += 1
        else:
            logger.warning(f"File not found for undo: {current}")
            error_count += 1

    logger.info(f"Undo completed - Success: {success_count}, Errors: {error_count}")

    print("\nCleaning up empty organizer folders...")
    logger.info("Cleaning up organizer-created folders only")

    categories = list(extensions.keys()) + ["Others"]

    for cat in categories:
        cat_folder = Path(target_folder) / cat

        if cat_folder.exists() and cat_folder.is_dir():
            try:
                _remove_empty_dirs(cat_folder)

                if not any(cat_folder.iterdir()):
                    cat_folder.rmdir()
                    print(f"Removed category folder: {cat_folder}")
                    logger.info(f"Removed category folder: {cat_folder}")

            except Exception as e:
                logger.debug(f"Failed to clean {cat_folder}: {e}")


def _remove_empty_dirs(path):
    """Recursively remove empty subdirectories (not the root)."""
    if not path.exists() or not path.is_dir():
        return

    for child in list(path.iterdir()):
        if child.is_dir():
            _remove_empty_dirs(child)

    if not any(path.iterdir()):
        return


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
      
  `organize "C:\\Users\\name\\Downloads" --dry-run`
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
    logger.info("")
    logger.info(f"=" * 60)
    logger.info(f"Organizer started - Folder: {folder_path}")
    logger.info(
        f"Arguments - Dry run: {args.dry_run}, Recursive: {args.recursive}, Undo: {args.undo}"
    )

    config_path = ensure_user_config()
    try:
        with open(config_path, "r") as f:
            extensions = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        print(f"ERROR: Could not load configuration file: {e}")
        sys.exit(1)

    if args.undo:
        logger.info(f"--- STARTING UNDO SESSION FOR {folder_path} ---")
        num = args.undo if isinstance(args.undo, int) else 10
        run_undo(LOG_FILE, folder_path, extensions, num)
        logger.info(f"--- ENDING UNDO SESSION FOR {folder_path} ---")
        return

    try:
        with FileOrganizerSession(folder_path) as session:
            print(f"Organizing folder: {folder_path}")
            print("")
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
        logger.critical(f"INVALID PATH: {e.foldername}")

    except Exception as e:
        print(f"UNCAPTURED ERROR: {e}")
        logger.error(f"UNCAPTURED EXCEPTION: {e}", exc_info=True)

    finally:
        if "folder_path" in locals():
            logger.info(f"--- ENDING SESSION FOR {folder_path} ---")
        config_file = get_user_config_dir() / "extensions.json"

        print(f"Config file used: {config_file}")
        print(f"Saved logs to: {LOG_FILE}")
        logger.info(f"=" * 60)


if __name__ == "__main__":
    main()
