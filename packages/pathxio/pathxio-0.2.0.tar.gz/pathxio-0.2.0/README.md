# Pathxio

**Safe, predictable filesystem operations for Python.**

Pathxio is a small, safety-first wrapper around common file operations like copy, move, and delete.
It helps you avoid destructive mistakes by making safe behavior the default.

---

## Why Pathx?

Python’s built-in filesystem tools (os, shutil) are powerful but easy to misuse:

- Overwrites happen silently
- Deletes are irreversible
- APIs are inconsistent
- Safety checks are manual

Pathxio flips that around.
If an operation looks dangerous, it fails loudly.

---

## Installation

    pip install pathxio

---

## Quick Start

### Safe Copy

    from pathxio import copy

    copy("src/", "dst/")

- Copies files or directories
- Fails if destination already exists
- Raises clear, readable errors

---

### Safe Move

    from pathxio import move

    move("old/", "new/")

- No overwrite by default
- Uses atomic moves when possible
- Explicit failure on unsafe operations

---

### Guarded Delete

    from pathxio import remove

    remove("build/")

By default, Pathx refuses to delete:
- root directories
- home directories
- non-empty directories

To force deletion:

    remove("build/", force=True)

---

### Dry Run Mode

Preview what would happen without touching the filesystem:

    copy("src/", "dst/", dry_run=True)

Returns a list of planned operations instead of executing them.

---

## API (MVP)

    copy(src, dst, *, dry_run=False)
    move(src, dst, *, dry_run=False)
    remove(path, *, force=False, dry_run=False)

---

## Design Principles

- Safety over convenience
- Fail fast and loudly
- No surprising defaults
- Readable exceptions over clever magic

---

## Note

- Please give me new ideas to maintain this project

## Important Notice: Remove Operations and Undo Limitations

**Undo functionality is NOT available for remove operations.**

### Why This Limitation Exists:
- **Irreversible Nature**: File deletion cannot be properly reversed without maintaining permanent backups
- **Storage Requirements**: Full file restoration would require significant storage space
- **Data Integrity**: Removing the original file makes recovery impossible without external backup systems

### Recommended Practice:
Always maintain backups of important files before performing removal operations. For critical data, implement your own backup strategy using tools like rsync, cp, or cloud storage solutions.

### Workaround for Critical Operations:
For critical files, implement your own backup strategy that creates copies before deletion, ensuring you can restore files if needed.

---

## License

MIT
