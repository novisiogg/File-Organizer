# File Organizer

A Python‑based tool that automatically sorts files in any directory into categorized folders based on file extensions.

## Overview

The tool scans a target directory, reads a configuration file that maps extensions to categories (e.g., `.jpg` → `Images`), and moves each file into the corresponding category. Unknown extensions go into an `Others` folder.

## Project Structure

```
file-organizer/
├── src/
│   └── organizer/
│       ├── __init__.py
│       ├── __main__.py          # main script
│       ├── logger.py
│       ├── exceptions.py
│       └── config/
│           └── extensions.json  # extensions
├── pyproject.toml
├── README.md
└── .gitignore
```

## Configuration (`extensions.json`)

The file is located at `src/organizer/config/extensions.json`.  
Example content:

```json
{
  "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
  "Videos": [".mp4", ".mov", ".mkv", ".avi"],
  "Documents": [".pdf", ".docx", ".txt", ".md"],
  "Audio": [".mp3", ".wav", ".flac"],
  "Archives": [".zip", ".tar", ".gz"],
  "Programming": [".py", ".js", ".html", ".css", ".cpp"],
  "Executables": [".exe", ".msi", ".app"],
  "Design": [".psd", ".ai", ".fig"]
}
```

You can easily add or remove extensions and categories.

## Installation

### From GitHub (recommended)

```bash
pip install git+https://github.com/novisiogg/file-organizer.git
```

### From source (for development)

```bash
git clone https://github.com/novisiogg/file-organizer.git
cd file-organizer
pip install -e .
```

After installation, the `organize` command is available system‑wide.

## Usage

```bash
organize <folder_path> 
```

| Option        | Description                                                           |
| :------------ | :-------------------------------------------------------------------- |
| `folder_path` | Path to the folder you want to organize (required).                   |
| `--dry-run`   | Preview what would be moved without actually moving files (optional). |

### Examples

```bash
# Organize your Documents folder
organize "C:\Users\users\Documents"

# Dry run – see what would happen
organize "C:\Users\Name\Desktop\Folder" --dry-run
```

## Features

- Recognizes **80+ file extensions** out of the box (extendable).
- **Automatic folder creation** – target category folders are created if missing.
- **Safe duplicate handling** – if a file name already exists, it is renamed with a `(1)`, `(2)`, etc.
- **Dry‑run mode** – preview changes before committing.
- **Protection for system folders** – refuses to run on `Windows`, `System32`, `Program Files`, etc.
- **Logging** – every move is logged to `~/.file_organizer/logs/app.log`.

## Customization

Edit `extensions.json` to add, remove, or change categories.  
The file is installed with the package; after modification, the new mapping is used immediately (no re‑installation required).

## Requirements

- Python 3.12 or higher
- No external dependencies (uses only the standard library)

---

**Tip:** The `extensions.json` obviously doesn't have every extension in the world, but it is designed to be easily customized.