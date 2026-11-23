import os
from pathlib import Path
import zipfile


class UnsafeArchiveError(ValueError):
    """Raised when an archive violates safety, path, or resource limits."""


def _is_within_directory(base_dir: Path, target_path: Path) -> bool:
    base_resolved = os.path.abspath(str(base_dir.resolve()))
    target_resolved = os.path.abspath(str(target_path.resolve()))
    try:
        return os.path.commonpath([base_resolved, target_resolved]) == base_resolved
    except ValueError:
        return False


def safe_extract_zip(
    zip_path: Path,
    dest_dir: Path,
    max_files: int = 2000,
    max_file_bytes: int = 5 * 1024 * 1024,
    max_total_bytes: int = 50 * 1024 * 1024,
    max_depth: int = 20,
) -> Path:
    """Safely extract a ZIP archive into dest_dir with strict guards."""
    zip_path = Path(zip_path)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    total_bytes = 0
    file_count = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        infos = zf.infolist()
        if len(infos) > max_files:
            raise UnsafeArchiveError(f"Archive exceeds max file count ({len(infos)} > {max_files}).")

        for info in infos:
            # Reject POSIX symlinks (S_IFLNK = 0o120000)
            unix_mode = (info.external_attr >> 16) & 0o170000
            if unix_mode == 0o120000:
                raise UnsafeArchiveError(f"Symlink entry not allowed: {info.filename}")

            if "\x00" in info.filename or info.filename.startswith(("/", "\\")):
                raise UnsafeArchiveError(f"Invalid archive member path: {info.filename}")

            parts = Path(info.filename).parts
            if ".." in parts:
                raise UnsafeArchiveError(f"Path traversal detected in member: {info.filename}")
            if len(parts) > max_depth:
                raise UnsafeArchiveError(f"Archive path too deep: {info.filename}")

            if info.file_size > max_file_bytes:
                raise UnsafeArchiveError(f"Member exceeds single-file cap: {info.filename}")

            total_bytes += info.file_size
            if total_bytes > max_total_bytes:
                raise UnsafeArchiveError("Archive exceeds cumulative extraction size limit.")

            target_path = dest_dir / info.filename
            if not _is_within_directory(dest_dir, target_path):
                raise UnsafeArchiveError(f"Resolved path escapes target directory: {info.filename}")

            if info.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue

            file_count += 1
            if file_count > max_files:
                raise UnsafeArchiveError("Extracted file count limit exceeded.")

            target_path.parent.mkdir(parents=True, exist_ok=True)
            written = 0
            with zf.open(info, "r") as src, open(target_path, "wb") as dst:
                while True:
                    chunk = src.read(65536)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_file_bytes:
                        raise UnsafeArchiveError(f"Actual uncompressed size exceeds cap: {info.filename}")
                    dst.write(chunk)

    return dest_dir
