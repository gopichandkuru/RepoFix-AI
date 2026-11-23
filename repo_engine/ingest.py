from dataclasses import dataclass
from pathlib import Path
from typing import List
from repo_engine.safe_extract import safe_extract_zip

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
}

SECRET_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}

SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore"}
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".pkl", ".pt", ".pth", ".safetensors",
}


@dataclass
class IngestedFile:
    rel_path: str
    size_bytes: int
    language: str


def detect_language(path: Path) -> str:
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".hpp": "cpp",
        ".h": "c_cpp_header",
        ".c": "c",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
    }
    return ext_map.get(path.suffix.lower(), "text")


def is_ignored_file(rel_path: Path, size_bytes: int, max_file_bytes: int = 1_000_000) -> bool:
    if any(part in IGNORED_DIRS for part in rel_path.parts):
        return True
    name_lower = rel_path.name.lower()
    if name_lower in SECRET_FILENAMES or name_lower.startswith(".env."):
        return True
    if rel_path.suffix.lower() in SECRET_SUFFIXES or rel_path.suffix.lower() in BINARY_SUFFIXES:
        return True
    if size_bytes > max_file_bytes:
        return True
    return False


def ingest_directory(repo_dir: Path, max_file_bytes: int = 1_000_000) -> List[IngestedFile]:
    repo_dir = Path(repo_dir).resolve()
    files: List[IngestedFile] = []
    for path in sorted(repo_dir.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(repo_dir)
        size_bytes = path.stat().st_size
        if is_ignored_file(rel, size_bytes, max_file_bytes=max_file_bytes):
            continue
        files.append(
            IngestedFile(
                rel_path=rel.as_posix(),
                size_bytes=size_bytes,
                language=detect_language(path),
            )
        )
    return files


def ingest_zip(zip_path: Path, extract_root: Path) -> List[IngestedFile]:
    extracted_dir = safe_extract_zip(zip_path, extract_root)
    return ingest_directory(extracted_dir)
