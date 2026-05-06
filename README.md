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
or 
```bash
# To organize the current directory
organize .
```

| Option                | Description                                            |
| :-------------------- | :----------------------------------------------------- |
| `folder_path`         | Path to the folder you want to organize (required)     |
| `--undo` or `-u`      | Undo changes (default = 10).                           |
| `--recursive` or `-r` | Sorts through subdirectories as well (default = false) |
| `--help` or `-h`      | Show a help message                                    |
### Examples

```bash
# Organize the current working directory
organize .

# Organize your Documents folder
organize "C:\Users\users\Documents"

# Organize your Documents folder and its subdirectories
organize "C:\Users\users\Documents" --recursive

# Dry run – see what would happen
organize "C:\Users\users\Desktop" -d -r

# Undo last 7 moves 
organize C:\Users\users\Desktop" -u 7
```

## Features

- Recognizes **80+ file extensions** out of the box (extendable).
- **Automatic folder creation** – target category folders are created if missing.
- **Safe duplicate handling** – if a file name already exists, it is renamed with a `(1)`, `(2)`, etc.
- **Dry‑run mode** – preview changes before committing.
- **Protection for system folders** – refuses to run on `Windows`, `System32`, `Program Files`, etc.
- **Logging** – every move is logged to `~/.file_organizer/logs/app.log` in case you want to undo the changes.

## Customization

To customize categories without losing changes when updating the package:

1. Once the script is launched it automatically creates user config file:
   - **Linux/macOS**: `~/.config/organizer/extensions.json`
   - **Windows**: `%APPDATA%\organizer\extensions.json`

2. Edit the file as you like – your changes will be remembered across package updates.


## Requirements

- Python 3.12 or higher
- No external dependencies (uses only the standard library)

---

**Tip:** The `extensions.json` obviously doesn't have every extension in the world, but it is designed to be easily customized.