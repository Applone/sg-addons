#!/usr/bin/env python3
"""Prepare pinned Swiftgram sources and apply the ordered patch series."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def configuration() -> dict[str, str]:
    data = json.loads((ROOT / "upstream.json").read_text(encoding="utf-8"))
    keys = {"repository", "version", "revision", "base_tree", "patched_tree"}
    if not isinstance(data, dict) or set(data) != keys:
        raise ValueError("upstream.json must contain: " + ", ".join(sorted(keys)))
    if not all(isinstance(value, str) and value for value in data.values()):
        raise ValueError("All upstream.json values must be nonempty strings")
    result: dict[str, str] = dict(data)
    if not result["repository"].startswith("https://"):
        raise ValueError("The upstream repository must use HTTPS")
    for key in ("revision", "base_tree", "patched_tree"):
        if not re.fullmatch(r"[0-9a-f]{40}", result[key]):
            raise ValueError(f"{key} must be a full Git SHA-1")
    return result


def series() -> list[Path]:
    directory = ROOT / "patches"
    patches: list[Path] = []
    for line in (directory / "series").read_text(encoding="utf-8").splitlines():
        name = line.partition("#")[0].strip()
        if not name:
            continue
        path = directory / name
        if (
            Path(name).is_absolute()
            or ".." in Path(name).parts
            or len(name.split()) != 1
            or path.suffix != ".patch"
            or not path.is_file()
            or not path.resolve().is_relative_to(directory.resolve())
        ):
            raise ValueError(f"Invalid patch in series: {name}")
        if path in patches:
            raise ValueError(f"Duplicate patch in series: {name}")
        path.read_text(encoding="utf-8")
        patches.append(path)
    if not patches or set(directory.rglob("*.patch")) != set(patches):
        raise ValueError("series must list every .patch exactly once")
    return patches


def git(source: Path, *args: str, env: dict[str, str] | None = None) -> str:
    return subprocess.check_output(["git", "-C", str(source), *args], text=True, env=env).strip()


def apply(source: Path, lock: dict[str, str], patches: list[Path]) -> None:
    if Path(git(source, "rev-parse", "--show-toplevel")).resolve() != source:
        raise ValueError("Source must be the root of its own Git checkout")
    if git(source, "rev-parse", "HEAD") != lock["revision"]:
        raise ValueError("Source HEAD does not match upstream.json revision")
    if git(source, "rev-parse", "HEAD^{tree}") != lock["base_tree"]:
        raise ValueError("Source tree does not match upstream.json base_tree")
    if git(source, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("Source must be clean; use a fresh checkout to reapply patches")

    # Validate the entire series and its final tree before changing the source checkout.
    with tempfile.TemporaryDirectory(prefix="sg-addons-index-") as temporary:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(temporary) / "index")}
        git(source, "read-tree", "HEAD", env=env)
        for patch in patches:
            git(source, "apply", "--cached", "--whitespace=error", str(patch), env=env)
        tree = git(source, "write-tree", env=env)
        if tree != lock["patched_tree"]:
            raise ValueError(f"Patched tree {tree} does not match upstream.json patched_tree")

    for patch in patches:
        git(source, "apply", "--index", "--whitespace=error", str(patch))
        print(f"Applied {patch.relative_to(ROOT)}", flush=True)
    print(f"Verified patched tree: {tree}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Validate the source lock and patch series")
    prepare = commands.add_parser("prepare", help="Fetch one upstream commit and apply patches")
    prepare.add_argument("source", type=Path, help="New directory; must not already exist")
    prepare.add_argument("--submodules", action="store_true", help="Fetch build dependencies")
    existing = commands.add_parser("apply", help="Patch an existing clean, pinned checkout")
    existing.add_argument("source", type=Path)
    args = parser.parse_args()
    try:
        lock, patches = configuration(), series()
        if args.command == "check":
            for patch in patches:
                git(ROOT, "apply", "--numstat", str(patch))
            print(f"Valid source lock and {len(patches)} patches")
            return 0

        source = args.source.resolve()
        if args.command == "prepare":
            source.mkdir(parents=True, exist_ok=False)
            git(source, "init", "--quiet")
            git(source, "remote", "add", "origin", lock["repository"])
            git(
                source,
                "-c",
                "gc.auto=0",
                "fetch",
                "--depth=1",
                "--no-tags",
                "--no-recurse-submodules",
                "origin",
                lock["revision"],
            )
            git(source, "checkout", "--quiet", "--detach", "FETCH_HEAD")
        apply(source, lock, patches)
        if args.command == "prepare" and args.submodules:
            git(source, "submodule", "update", "--init", "--recursive", "--depth=1")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
