"""Utility functions for agents.lock."""

from __future__ import annotations  # noqa: I001

import hashlib
import logging
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict
from collections.abc import Iterator

logger = logging.getLogger("agentslock")


def setup_logging(verbose: bool = False, no_color: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(levelname)s: %(message)s" if no_color else "%(message)s"
    logging.basicConfig(level=level, format=fmt)


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def content_hash(content: str | bytes) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def directory_hash(path: Path) -> str:
    h = hashlib.sha256()
    for root, _, files in sorted(os.walk(path)):
        for fname in sorted(files):
            fpath = Path(root) / fname
            rel = fpath.relative_to(path)
            h.update(str(rel).encode("utf-8"))
            h.update(file_hash(fpath).encode("utf-8"))
    return h.hexdigest()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_remove(path: Path) -> None:
    if path.is_file() or path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def atomic_write(path: Path, content: str | bytes, encoding: str = "utf-8") -> None:
    ensure_dir(path.parent)
    mode = "w" if isinstance(content, str) else "wb"
    suffix = path.suffix or ".tmp"

    with tempfile.NamedTemporaryFile(
        mode=mode,
        encoding=encoding if isinstance(content, str) else None,
        dir=path.parent,
        suffix=suffix,
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        tmp_path.replace(path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)


@contextmanager
def temp_directory() -> Iterator[Path]:
    tmp = Path(tempfile.mkdtemp(prefix="agentslock_"))
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def normalize_path(path: str | Path, relative_to: Path | None = None) -> Path:
    p = Path(path).expanduser()
    if p.is_absolute():
        if relative_to:
            try:
                return p.relative_to(relative_to)
            except ValueError:
                return p
        return p
    return p


def resolve_relative_path(path: str | Path, base: Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (base / p).resolve()


def is_subpath(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def find_closest_match(value: str, options: list[str], threshold: float = 0.6) -> str | None:
    value_lower = value.lower()
    best_match = None
    best_score = 0.0

    for opt in options:
        opt_lower = opt.lower()
        # Simple prefix/substring matching
        if opt_lower.startswith(value_lower):
            score = len(value_lower) / len(opt_lower)
            if score > best_score:
                best_score = score
                best_match = opt
        elif value_lower in opt_lower:
            score = len(value_lower) / len(opt_lower) * 0.8
            if score > best_score:
                best_score = score
                best_match = opt

    if best_score >= threshold:
        return best_match
    return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    atomic_write(path, content)


class ParsedGitUrl(TypedDict):
    repo: str
    ref: str | None
    subdir: str
    file: str


def parse_github_url(url: str) -> ParsedGitUrl:
    """
    Parse a GitHub URL and extract repo, ref, and subdir.

    Handles URLs like:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/tree/main/path/to/dir
    - https://github.com/owner/repo/blob/main/path/to/file
    - git@github.com:owner/repo.git

    Returns dict with keys: repo, ref, subdir, file
    """
    import re
    from urllib.parse import urlparse

    result: ParsedGitUrl = {"repo": url, "ref": None, "subdir": "", "file": ""}

    # Handle git@ SSH URLs
    if url.startswith("git@"):
        # git@github.com:owner/repo.git -> https://github.com/owner/repo
        match = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", url)
        if match:
            host, path = match.groups()
            result["repo"] = f"https://{host}/{path}"
            return result
        result["repo"] = url
        return result

    parsed = urlparse(url)

    # Check if it's a GitHub URL with tree/blob path
    if "github.com" in parsed.netloc:
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1]
            if repo.endswith(".git"):
                repo = repo[:-4]

            result["repo"] = f"https://github.com/{owner}/{repo}"

            # Check for tree/blob pattern
            if len(path_parts) >= 4 and path_parts[2] in ("tree", "blob"):
                result["ref"] = path_parts[3]
                if len(path_parts) > 4:
                    subpath = "/".join(path_parts[4:])
                    if path_parts[2] == "blob":
                        result["file"] = subpath
                    else:
                        result["subdir"] = subpath

            return result

    # Handle other git hosting services with similar patterns (GitLab, etc.)
    if "/tree/" in url or "/blob/" in url:
        # Split on tree/ or blob/
        if "/tree/" in url:
            base, rest = url.split("/tree/", 1)
            parts = rest.split("/", 1)
            result["repo"] = base
            result["ref"] = parts[0]
            if len(parts) > 1:
                result["subdir"] = parts[1]
        elif "/blob/" in url:
            base, rest = url.split("/blob/", 1)
            parts = rest.split("/", 1)
            result["repo"] = base
            result["ref"] = parts[0]
            if len(parts) > 1:
                result["file"] = parts[1]
        return result

    # Plain URL - use as-is
    if url.endswith(".git"):
        result["repo"] = url[:-4]
    else:
        result["repo"] = url.rstrip("/")

    return result

