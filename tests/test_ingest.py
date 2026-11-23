from pathlib import Path
import zipfile
import pytest

from repo_engine.ingest import ingest_directory, ingest_zip
from repo_engine.safe_extract import UnsafeArchiveError, safe_extract_zip


def test_safe_extract_rejects_path_traversal(tmp_path: Path):
    evil_zip = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil_zip, "w") as zf:
        zf.writestr("../escaped.txt", "malicious")

    with pytest.raises(UnsafeArchiveError):
        safe_extract_zip(evil_zip, tmp_path / "extracted")


def test_safe_extract_rejects_symlink(tmp_path: Path):
    sym_zip = tmp_path / "symlink.zip"
    info = zipfile.ZipInfo("link_to_etc")
    info.create_system = 3  # Unix
    info.external_attr = (0o120777 << 16)
    with zipfile.ZipFile(sym_zip, "w") as zf:
        zf.writestr(info, "/etc/passwd")

    with pytest.raises(UnsafeArchiveError):
        safe_extract_zip(sym_zip, tmp_path / "extracted")


def test_ingest_filters_secrets_and_ignored_dirs(tmp_path: Path):
    repo = tmp_path / "sample_repo"
    (repo / "src").mkdir(parents=True)
    (repo / ".git").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (repo / ".env").write_text("SECRET_KEY=123\n", encoding="utf-8")
    (repo / ".git" / "config").write_text("[core]\n", encoding="utf-8")

    files = ingest_directory(repo)
    rel_paths = [f.rel_path for f in files]

    assert rel_paths == ["src/app.py"]
    assert files[0].language == "python"


def test_ingest_valid_zip(tmp_path: Path):
    good_zip = tmp_path / "good.zip"
    with zipfile.ZipFile(good_zip, "w") as zf:
        zf.writestr("pkg/math_utils.py", "def add(a, b):\n    return a + b\n")
        zf.writestr("pkg/.env", "TOKEN=abc\n")

    files = ingest_zip(good_zip, tmp_path / "out")
    assert [f.rel_path for f in files] == ["pkg/math_utils.py"]
