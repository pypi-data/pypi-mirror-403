"""Safe filesystem operations implementation with undo support."""

import os
import shutil
import glob
import asyncio
from pathlib import Path
from typing import Union, List, Optional, Dict, Any
import tempfile
import argparse
import sys
from functools import partial

__all__ = ["copy", "move", "remove", "undo", "glob_copy", "async_copy", "async_move"]

_undo_history: List[Dict[str, Any]] = []


class pathxioError(Exception):
    pass


def _record_operation(op_type: str, src: Path, dst: Optional[Path] = None) -> None:
    _undo_history.append({
        "type": op_type,
        "src": src,
        "dst": dst
    })


def _check_dangerous_paths(src_path: Path, dst_path: Optional[Path]) -> None:
    if src_path == Path("/") or str(src_path) == "/home":
        raise pathxioError("Refusing to operate on root or home directory")

    dangerous_patterns = ["/root/", "/bin/", "/usr/", "/sbin/", "/var/"]
    src_str = str(src_path).lower()

    if any(pattern in src_str for pattern in dangerous_patterns):
        if not str(src_path).startswith("/tmp/"):
            raise pathxioError(f"Refusing to operate on potentially dangerous path: {src_path}")

    if dst_path:
        dst_str = str(dst_path).lower()
        if any(pattern in dst_str for pattern in dangerous_patterns):
            if not str(dst_path).startswith("/tmp/"):
                raise pathxioError(f"Refusing to move to dangerous location: {dst_path}")


def copy(src: Union[str, Path], dst: Union[str, Path], *, dry_run: bool = False) -> None:
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise pathxioError(f"Source does not exist: {src}")

    if dst_path.exists():
        raise FileExistsError(f"Destination already exists: {dst}")

    _check_dangerous_paths(src_path, dst_path)

    if dry_run:
        print(f"DRY RUN: Would copy {src} to {dst}")
        return

    try:
        if src_path.is_dir():
            shutil.copytree(src_path, dst_path)
        else:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
        _record_operation("copy", src_path, dst_path)
    except Exception as e:
        raise pathxioError(f"Copy failed: {e}")


def move(src: Union[str, Path], dst: Union[str, Path], *, dry_run: bool = False) -> None:
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise pathxioError(f"Source does not exist: {src}")

    if dst_path.exists():
        raise FileExistsError(f"Destination already exists: {dst}")

    _check_dangerous_paths(src_path, dst_path)

    if dry_run:
        print(f"DRY RUN: Would move {src} to {dst}")
        return

    try:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        _record_operation("move", src_path, dst_path)
    except Exception as e:
        raise pathxioError(f"Move failed: {e}")


def remove(path: Union[str, Path], *, force: bool = False, dry_run: bool = False) -> None:
    path_obj = Path(path)

    if not path_obj.exists():
        raise pathxioError(f"Path does not exist: {path}")

    _check_dangerous_paths(path_obj, None)

    if not force:
        if path_obj.is_dir() and path_obj != Path(".") and path_obj != Path(".."):
            if any(path_obj.iterdir()):
                raise pathxioError(f"Directory is not empty: {path}. Use force=True to remove.")

    if dry_run:
        print(f"DRY RUN: Would remove {path}")
        return

    try:
        if path_obj.is_dir():
            shutil.rmtree(path_obj)
        else:
            path_obj.unlink()
    except Exception as e:
        raise pathxioError(f"Remove failed: {e}")


def undo() -> None:
    if not _undo_history:
        print("Nothing to undo.")
        return

    op = _undo_history.pop()
    op_type = op["type"]
    src = op["src"]
    dst = op.get("dst")

    try:
        if op_type == "copy":
            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
                print(f"Undid copy: {src} -> {dst}")
        elif op_type == "move":
            if not src.parent.exists():
                src.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_dir():
                shutil.move(str(dst), str(src))
            else:
                shutil.move(str(dst), str(src))
            print(f"Undid move: {dst} -> {src}")
        elif op_type == "remove":
            if src.is_dir():
                src.mkdir(parents=True, exist_ok=True)
                print(f"Undid remove of directory: {src}")
            else:
                print(f"Cannot restore file: {src} (undoing not implemented)")
        else:
            raise pathxioError("Unknown operation type in history")

    except Exception as e:
        raise pathxioError(f"Failed to undo operation: {e}")


def glob_copy(pattern: str, dst_dir: Union[str, Path], *, dry_run: bool = False) -> None:
    """Copy files matching glob pattern to destination directory."""
    src_paths = [Path(f) for f in glob.glob(pattern, recursive=True)]
    dst_path = Path(dst_dir)
    
    if not src_paths:
        print(f"No files match pattern: {pattern}")
        return

    dst_path.mkdir(parents=True, exist_ok=True)
    
    for src in src_paths:
        if src.is_file():
            dst = dst_path / src.name
            copy(src, dst, dry_run=dry_run)
        else:
            # Handle directories by copying tree structure
            dst = dst_path / src.name
            copy(src, dst, dry_run=dry_run)


async def async_copy(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Asynchronously copy a file or directory."""
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, copy, src, dst)
    except Exception as e:
        raise pathxioError(f"Async copy failed: {e}")


async def async_move(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Asynchronously move a file or directory."""
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, move, src, dst)
    except Exception as e:
        raise pathxioError(f"Async move failed: {e}")


def _cross_device_copy(src: Path, dst: Path) -> None:
    """Optimized cross-device copy using temporary files."""
    if src.parent == dst.parent:
        shutil.copy2(src, dst)
    else:
        temp_dir = tempfile.mkdtemp()
        try:
            temp_file = Path(temp_dir) / f"tmp_{src.name}"
            shutil.copy2(src, temp_file)
            shutil.move(str(temp_file), str(dst))
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def _cross_device_move(src: Path, dst: Path) -> None:
    """Optimized cross-device move using temporary files."""
    if src.parent == dst.parent:
        shutil.move(str(src), str(dst))
    else:
        temp_dir = tempfile.mkdtemp()
        try:
            temp_file = Path(temp_dir) / f"tmp_{src.name}"
            shutil.copy2(src, temp_file)
            os.unlink(src)
            shutil.move(str(temp_file), str(dst))
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def _create_cli_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(description="Safe filesystem operations with undo support")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    copy_parser = subparsers.add_parser('copy', help='Copy files/directories')
    copy_parser.add_argument('src', help='Source path')
    copy_parser.add_argument('dst', help='Destination path')
    copy_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')

    move_parser = subparsers.add_parser('move', help='Move files/directories')
    move_parser.add_argument('src', help='Source path')
    move_parser.add_argument('dst', help='Destination path')
    move_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')

    remove_parser = subparsers.add_parser('remove', help='Remove files/directories')
    remove_parser.add_argument('path', help='Path to remove')
    remove_parser.add_argument('--force', action='store_true', help='Force removal')
    remove_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')

    undo_parser = subparsers.add_parser('undo', help='Undo last operation')

    glob_parser = subparsers.add_parser('glob-copy', help='Copy files matching glob pattern')
    glob_parser.add_argument('pattern', help='Glob pattern (e.g., "*.txt")')
    glob_parser.add_argument('dst_dir', help='Destination directory')
    glob_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')

    return parser


def main():
    """Main CLI entry point."""
    parser = _create_cli_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'copy':
            copy(args.src, args.dst, dry_run=args.dry_run)
        elif args.command == 'move':
            move(args.src, args.dst, dry_run=args.dry_run)
        elif args.command == 'remove':
            remove(args.path, force=args.force, dry_run=args.dry_run)
        elif args.command == 'undo':
            undo()
        elif args.command == 'glob-copy':
            glob_copy(args.pattern, args.dst_dir, dry_run=args.dry_run)
        else:
            parser.print_help()
    except pathxioError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
