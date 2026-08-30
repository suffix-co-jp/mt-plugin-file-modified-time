#!/usr/bin/env python3
"""Build a deterministic FileModifiedTime distribution directory and ZIP archive."""

from __future__ import annotations

import re
import shutil
import stat
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PACKAGE_NAME = "FileModifiedTime"
PACKAGE_ROOT = DIST / PACKAGE_NAME
INCLUDE = (
    "config.yaml",
    "lib",
    "README.md",
)


def plugin_version() -> str:
    config = (ROOT / "config.yaml").read_text(encoding="utf-8")
    match = re.search(r"(?m)^version:\s*([0-9]+(?:\.[0-9]+)+)\s*$", config)
    if not match:
        raise RuntimeError("config.yaml does not contain a valid version")
    return match.group(1)


def reset_dist() -> None:
    resolved = DIST.resolve()
    if resolved.parent != ROOT or resolved.name != "dist":
        raise RuntimeError(f"Refusing to replace unexpected directory: {resolved}")
    if DIST.exists():
        shutil.rmtree(DIST)
    PACKAGE_ROOT.mkdir(parents=True)


def copy_package() -> None:
    for relative in INCLUDE:
        source = ROOT / relative
        if not source.exists():
            raise RuntimeError(f"Required distribution input is missing: {relative}")
        destination = PACKAGE_ROOT / relative
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)


def normalized_entries() -> list[Path]:
    entries = [PACKAGE_ROOT]
    entries.extend(sorted(PACKAGE_ROOT.rglob("*"), key=lambda path: path.as_posix()))
    return entries


def zip_info(archive_name: str, is_dir: bool, build_timestamp: tuple[int, ...]) -> zipfile.ZipInfo:
    if is_dir and not archive_name.endswith("/"):
        archive_name += "/"
    info = zipfile.ZipInfo(archive_name, build_timestamp)
    info.create_system = 3
    mode = (stat.S_IFDIR | 0o755) if is_dir else (stat.S_IFREG | 0o644)
    info.external_attr = mode << 16
    if is_dir:
        info.external_attr |= 0x10
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def build_zip(version: str, entries: list[Path], build_timestamp: tuple[int, ...]) -> Path:
    archive = DIST / f"{PACKAGE_NAME}-{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in entries:
            relative = path.relative_to(DIST).as_posix()
            info = zip_info(relative, path.is_dir(), build_timestamp)
            output.writestr(info, b"" if path.is_dir() else path.read_bytes())
    return archive


def verify_zip(archive: Path, entries: list[Path], build_timestamp: tuple[int, ...]) -> None:
    expected = {
        path.relative_to(DIST).as_posix() + ("/" if path.is_dir() else "")
        for path in entries
    }
    with zipfile.ZipFile(archive) as package:
        actual = {info.filename for info in package.infolist()}
        if actual != expected:
            raise RuntimeError("Distribution ZIP contents do not match the expanded package")
        for info in package.infolist():
            if not info.filename.startswith(f"{PACKAGE_NAME}/"):
                raise RuntimeError(f"Invalid archive root: {info.filename}")
            if info.date_time != build_timestamp:
                raise RuntimeError(f"Unexpected timestamp: {info.filename}")
            expected_mode = 0o755 if info.is_dir() else 0o644
            actual_mode = (info.external_attr >> 16) & 0o777
            if actual_mode != expected_mode:
                raise RuntimeError(f"Invalid permissions for {info.filename}: {actual_mode:o}")
            if not info.is_dir():
                expanded = DIST / info.filename
                if package.read(info) != expanded.read_bytes():
                    raise RuntimeError(f"Archive content mismatch: {info.filename}")


def main() -> None:
    version = plugin_version()
    now = datetime.now()
    build_timestamp = (now.year, now.month, now.day, now.hour, now.minute, now.second - (now.second % 2))
    reset_dist()
    copy_package()
    entries = normalized_entries()
    archive = build_zip(version, entries, build_timestamp)
    verify_zip(archive, entries, build_timestamp)
    print(f"Expanded: {PACKAGE_ROOT}")
    print(f"Archive:  {archive}")
    print("Verified: archive root, contents, permissions, and build timestamps")


if __name__ == "__main__":
    main()
