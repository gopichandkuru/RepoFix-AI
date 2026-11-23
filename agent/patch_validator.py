from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import List

_DIFF_FILE_RE = re.compile(r"^(?:\+\+\+|---)\s+(?:a/|b/)?([^\t\n]+)")


class PatchValidationError(ValueError):
    """Raised when a proposed diff is malformed or targets unsafe paths."""


@dataclass
class ParsedPatch:
    target_files: List[str]
    raw_diff: str
    hunk_count: int


def _is_safe_rel_path(repo_root: Path, rel_file: str) -> bool:
    cleaned = rel_file.strip()
    if not cleaned or cleaned == "/dev/null":
        return True
    if cleaned.startswith(("/", "\\")) or "\x00" in cleaned:
        return False
    p = Path(cleaned)
    if ".." in p.parts:
        return False
    base = os.path.abspath(str(repo_root.resolve()))
    target = os.path.abspath(str((repo_root / p).resolve()))
    try:
        return os.path.commonpath([base, target]) == base
    except ValueError:
        return False


def validate_unified_diff(raw_diff: str, repo_root: Path) -> ParsedPatch:
    """Validate unified diff structure and ensure all modified paths stay inside repo_root."""
    if not raw_diff or not raw_diff.strip():
        raise PatchValidationError("Patch diff is empty.")

    lines = raw_diff.splitlines()
    target_files: List[str] = []
    hunk_count = 0

    for line in lines:
        if line.startswith("@@"):
            hunk_count += 1
        m = _DIFF_FILE_RE.match(line)
        if m:
            raw_target = m.group(1).strip()
            if raw_target != "/dev/null":
                if not _is_safe_rel_path(repo_root, raw_target):
                    raise PatchValidationError(f"Unsafe or escaping patch target path: {raw_target}")
                if raw_target not in target_files:
                    target_files.append(raw_target)

    if hunk_count == 0 or not target_files:
        raise PatchValidationError("Invalid unified diff: missing file headers or @@ hunks.")

    return ParsedPatch(target_files=target_files, raw_diff=raw_diff, hunk_count=hunk_count)


def apply_unified_diff_to_text(original_text: str, raw_diff: str) -> str:
    """Apply a single-file unified diff cleanly with line-context checks."""
    lines = original_text.splitlines(keepends=True)
    diff_lines = raw_diff.splitlines()

    idx = 0
    while idx < len(diff_lines) and not diff_lines[idx].startswith("@@"):
        idx += 1

    if idx >= len(diff_lines):
        raise PatchValidationError("No @@ hunk found in diff.")

    out_lines: List[str] = []
    src_pos = 0

    while idx < len(diff_lines):
        header = diff_lines[idx]
        m = re.match(r"^@@\s+-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@", header)
        if not m:
            raise PatchValidationError(f"Malformed hunk header: {header}")
        orig_start = max(0, int(m.group(1)) - 1)
        if orig_start > len(lines):
            raise PatchValidationError("Hunk start exceeds file length.")

        out_lines.extend(lines[src_pos:orig_start])
        src_pos = orig_start
        idx += 1

        while idx < len(diff_lines) and not diff_lines[idx].startswith("@@"):
            dline = diff_lines[idx]
            idx += 1
            if dline.startswith("\\"):
                continue
            if not dline:
                continue
            prefix = dline[0]
            content = dline[1:]
            eol = "\n"

            if prefix == " ":
                if src_pos >= len(lines) or lines[src_pos].rstrip("\r\n") != content:
                    raise PatchValidationError(f"Context mismatch at line {src_pos + 1}.")
                out_lines.append(lines[src_pos])
                src_pos += 1
            elif prefix == "-":
                if src_pos >= len(lines) or lines[src_pos].rstrip("\r\n") != content:
                    raise PatchValidationError(f"Deletion mismatch at line {src_pos + 1}.")
                src_pos += 1
            elif prefix == "+":
                out_lines.append(content + eol)
            else:
                raise PatchValidationError(f"Unexpected diff line prefix: {prefix}")

    out_lines.extend(lines[src_pos:])
    result = "".join(out_lines)
    if not original_text.endswith("\n") and result.endswith("\n"):
        result = result[:-1]
    return result
