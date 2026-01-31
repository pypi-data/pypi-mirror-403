#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import yaml
from pathlib import Path
from typing import Iterable, List, Optional, Any, Dict, Callable, Set, Mapping
from functools import lru_cache

from dumpster.git_utils import (
    batch_git_ignored,
    build_gitignore_set,
    git_ignored_set,
    git_repo,
    is_git_ignored,
    get_git_metadata,
    render_git_metadata,
)
from dumpster.logs import getLogger
from dumpster.models import DumpsterConfig
from dumpster.const import DEFAULT_TEXT_EXTENSIONS, FILE_SEPARATOR

logger = getLogger(__name__)


ROOT = Path(os.getenv("DUMPSTER_ROOT", Path.cwd().resolve()))
CONFIG_FILE = Path(os.getenv("DUMPSTER_CONFIG", ROOT / "dump.yaml"))


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    value = re.sub(r"^-+|-+$", "", value)
    return value or "dump"


def _load_yaml_dict(config_file: Path) -> Dict[str, Any]:
    if not config_file.exists():
        raise FileNotFoundError(f"{config_file} not found")

    with open(config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("dump.yaml must be a YAML mapping/object at the top level")

    return data


def _compile_name_matcher(pattern: str) -> Callable[[str], bool]:
    """
    Matches dump item name using:
      1) regex fullmatch (case-insensitive) if pattern compiles
      2) else exact case-insensitive match
      3) plus a substring fallback (case-insensitive) for convenience
    """
    pattern = (pattern or "").strip()
    if not pattern:
        return lambda _: True

    try:
        rx = re.compile(pattern, re.IGNORECASE)

        def _match(name: str) -> bool:
            n = name or ""
            return bool(rx.fullmatch(n) or rx.search(n))

        return _match
    except re.error:
        lower = pattern.lower()

        def _match(name: str) -> bool:
            n = (name or "").lower()
            return n == lower or lower in n

        return _match


@lru_cache(maxsize=1)
def load_config(config_file: Path | str | None = None) -> DumpsterConfig:
    """
    Single-config loader (ignores `dumps:` if present).
    Kept for backwards compatibility and existing tests.
    """
    config_file = Path(config_file or CONFIG_FILE)
    data = _load_yaml_dict(config_file)
    if "dumps" in data:
        data = {k: v for k, v in data.items() if k != "dumps"}
    return DumpsterConfig.model_validate(data)


def _extensions_from_config(config: DumpsterConfig) -> set[str]:
    if config.extensions is not None:
        return {e.lower() for e in config.extensions}
    return DEFAULT_TEXT_EXTENSIONS


def is_text_file(path: Path, extensions: set[str]) -> bool:
    return path.suffix.lower() in extensions


def should_skip(path: Path, extensions: set[str]) -> bool:
    if path.is_dir():
        return True
    if not is_text_file(path, extensions):
        return True
    if is_git_ignored(path):
        return True
    return False


def expand_content_entry(entry: str, root_path: Path) -> List[Path]:
    """
    Expansion rules:
      - directory → recursive include (dir/**)
      - glob pattern → glob expansion
      - file → include file
    """
    entry = entry.strip()
    path = (root_path / entry).resolve()

    # Explicit glob pattern
    if any(ch in entry for ch in ["*", "?", "["]):
        return sorted(root_path.glob(entry))

    if path.is_dir():
        return sorted(path.rglob("*"))

    if path.is_file():
        return [path]

    return []


def _is_glob(entry: str) -> bool:
    return any(ch in entry for ch in ["*", "?", "["])


def iter_content_files(
    entries: Iterable[str],
    root_path: Path,
    extensions: set[str],
) -> List[Path]:
    # Identify *explicit* files passed by the user (no glob, and is a file)
    explicit_files: Set[Path] = set()
    for entry in entries:
        e = (entry or "").strip()
        if not e or _is_glob(e):
            continue
        p = (root_path / e).resolve()
        if p.is_file():
            explicit_files.add(p)

    # Expand entries (same as before), but keep everything for now
    expanded: List[Path] = []
    for entry in entries:
        expanded.extend(expand_content_entry(entry, root_path))

    # Dedup while preserving order (avoid huge set churn early)
    seen_any: Set[Path] = set()
    deduped: List[Path] = []
    for p in expanded:
        if p not in seen_any:
            seen_any.add(p)
            deduped.append(p)

    # Prepare a list of non-explicit candidate files that need filtering
    candidates_for_ignore: List[Path] = []
    for p in deduped:
        if p in explicit_files:
            continue
        if p.is_file() and is_text_file(p, extensions):
            candidates_for_ignore.append(p)

    # Batch compute gitignored for candidates (fast)
    repo = git_repo(root_path)
    ignored_rel: Set[str] = set()
    if repo:
        ignored_rel = batch_git_ignored(repo, candidates_for_ignore)

    # Final filtering: match existing should_skip logic, but use the batch set
    result: List[Path] = []
    seen_out: Set[Path] = set()
    repo_wd = Path(repo.working_dir) if repo else None

    for p in deduped:
        if p in seen_out:
            continue

        # If user explicitly listed a file, trust it (same behavior as current code)
        if p in explicit_files:
            if p.is_file():
                result.append(p)
                seen_out.add(p)
            continue

        # Otherwise apply the standard filters
        if p.is_dir():
            continue
        if not is_text_file(p, extensions):
            continue

        if repo and repo_wd:
            try:
                rel = str(p.relative_to(repo_wd))
                if rel in ignored_rel:
                    continue
            except Exception:
                # outside repo => behave like "not ignored"
                pass

        result.append(p)
        seen_out.add(p)

    return sorted(result)


def _write_dump(
    *,
    root_path: Path,
    config: DumpsterConfig,
    contents_override: Optional[List[str]] = None,
) -> Path:
    effective_contents = (
        contents_override if contents_override is not None else config.contents
    )
    extensions = _extensions_from_config(config)
    files = iter_content_files(effective_contents, root_path, extensions)

    git_meta = get_git_metadata(root_path)

    outfile = (root_path / config.output).resolve()
    outfile.parent.mkdir(parents=True, exist_ok=True)

    with open(outfile, "w", encoding="utf-8") as out:

        if config.prompt:
            out.write(config.prompt.strip() + "\n\n")

        if config.header:
            out.write(config.header.strip() + "\n\n")

        out.write(render_git_metadata(git_meta) + "\n\n")

        for file in files:
            rel = file.relative_to(root_path)
            out.write(f"\n{FILE_SEPARATOR} {rel}\n")
            out.write(file.read_text(encoding="utf-8", errors="ignore"))
            out.write("\n")

        if config.footer:
            out.write("\n" + config.footer.strip() + "\n")

    logger.info(f"Wrote {len(files)} files to {outfile}")
    return outfile


def _build_tree(paths: List[Path], *, root: Path) -> str:
    """
    Render a tree (like unix `tree`) of repo-relative file paths.
    Directories are inferred from file paths.
    """
    rels = [p.relative_to(root) for p in paths]
    # Trie node: dict[name -> children], where children is another dict; files are leaf nodes with {}
    trie: dict[str, dict] = {}

    for rp in rels:
        parts = list(rp.parts)
        node = trie
        for part in parts:
            node = node.setdefault(part, {})

    def _sorted_items(d: dict[str, dict]) -> list[tuple[str, dict]]:
        # Show directories first (non-empty dict), then files
        items = list(d.items())
        items.sort(key=lambda kv: (0 if kv[1] else 1, kv[0].lower()))
        return items

    lines: list[str] = []

    def _walk(node: dict[str, dict], prefix: str = "") -> None:
        items = _sorted_items(node)
        for idx, (name, child) in enumerate(items):
            last = idx == len(items) - 1
            branch = "└── " if last else "├── "
            lines.append(prefix + branch + name)
            if child:
                extension = "    " if last else "│   "
                _walk(child, prefix + extension)

    _walk(trie, "")
    return "\n".join(lines)


def resolve_dump_files(
    root_path: Path | str | None = None,
    config_file: Path | str | None = None,
    contents: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> Dict[str, List[Path]]:
    """
    Resolve the list of files that would be included, without writing output.

    Returns:
      dict(profile_name -> sorted list[Path]) where Paths are absolute.
      In single-config mode, the profile name is "default" (or config.name if set).
    """
    root_path = Path(root_path or ROOT)

    if not config_file:
        config_file = root_path / "dump.yaml"
    config_file = Path(config_file)

    raw = _load_yaml_dict(config_file)
    results: Dict[str, List[Path]] = {}

    dumps = raw.get("dumps")
    if isinstance(dumps, list) and dumps:
        defaults = {k: v for k, v in raw.items() if k not in ("dumps", "output")}
        matcher = _compile_name_matcher(name) if name else (lambda _: True)

        selected: List[Dict[str, Any]] = []
        for i, item in enumerate(dumps):
            if not isinstance(item, dict):
                logger.warning(
                    f"Skipping dumps[{i}] because it is not a mapping/object"
                )
                continue
            item_name = item.get("name")
            if not isinstance(item_name, str) or not item_name.strip():
                raise ValueError(f"dumps[{i}] is missing a valid 'name' field")
            if matcher(item_name):
                selected.append(item)

        if name and not selected:
            raise ValueError(f"No dump profiles matched --name {name!r}")

        for item in selected:
            item_name = item["name"].strip()
            merged = dict(defaults)
            merged.update(item)
            merged["name"] = item_name

            config = DumpsterConfig.model_validate(merged)
            effective_contents = contents if contents is not None else config.contents
            extensions = _extensions_from_config(config)
            files = iter_content_files(effective_contents, root_path, extensions)
            results[item_name] = files

        return results

    # Single-config mode
    config = DumpsterConfig.model_validate(raw)
    effective_contents = contents if contents is not None else config.contents
    extensions = _extensions_from_config(config)
    files = iter_content_files(effective_contents, root_path, extensions)
    results[
        (
            config.name.strip()
            if isinstance(config.name, str) and config.name.strip()
            else "default"
        )
    ] = files
    return results


def tree(
    root_path: Path | str | None = None,
    config_file: Path | str | None = None,
    contents: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> str:
    """
    Return a human-readable tree of files that would be included in the dump.
    In multi-profile mode, prints each profile separately.
    """
    root_path = Path(root_path or ROOT)
    profiles = resolve_dump_files(
        root_path=root_path, config_file=config_file, contents=contents, name=name
    )

    chunks: list[str] = []
    for profile_name in sorted(profiles.keys(), key=lambda s: s.lower()):
        files = profiles[profile_name]
        header = f"{profile_name} ({len(files)} files)"
        chunks.append(header)
        if files:
            chunks.append(_build_tree(files, root=root_path))
        else:
            chunks.append("└── (no files)")
        chunks.append("")  # blank line

    return "\n".join(chunks).rstrip() + "\n"


def dump(
    root_path: Path | str | None = None,
    config_file: Path | str | None = None,
    contents: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> List[Path]:
    """
    - If `dumps:` exists: process each item (optionally filtered by --name pattern).
      Root-level options act as defaults for items if not specified, EXCEPT `output`.
      If an item has no output, it becomes: <slug(name)>.txt
    - If no `dumps:`: process top-level options as a single item.
    Returns list of output paths written.
    """
    root_path = Path(root_path or ROOT)

    if not config_file:
        config_file = root_path / "dump.yaml"
    config_file = Path(config_file)

    raw = _load_yaml_dict(config_file)
    outputs: List[Path] = []

    dumps = raw.get("dumps")
    if isinstance(dumps, list) and dumps:
        # Root-level defaults for all dump items, excluding output (explicitly not a default).
        # If "only dumps exists", this dict is empty (good).
        defaults = {k: v for k, v in raw.items() if k not in ("dumps", "output")}

        matcher = _compile_name_matcher(name) if name else (lambda _: True)

        selected: List[Dict[str, Any]] = []
        for i, item in enumerate(dumps):
            if not isinstance(item, dict):
                logger.warning(
                    f"Skipping dumps[{i}] because it is not a mapping/object"
                )
                continue
            item_name = item.get("name")
            if not isinstance(item_name, str) or not item_name.strip():
                raise ValueError(f"dumps[{i}] is missing a valid 'name' field")
            if matcher(item_name):
                selected.append(item)

        if name and not selected:
            raise ValueError(f"No dump profiles matched --name {name!r}")

        for item in selected:
            item_name = item["name"].strip()
            merged = dict(defaults)
            merged.update(item)

            # output is NOT inherited from root; compose if missing
            if "output" not in item or not str(item.get("output") or "").strip():
                merged["output"] = f".dumpster/{_slugify(item_name)}.txt"

            # Ensure the config has its name
            merged["name"] = item_name

            config = DumpsterConfig.model_validate(merged)
            outputs.append(
                _write_dump(
                    root_path=root_path, config=config, contents_override=contents
                )
            )

        return outputs

    # Single-config mode: process top-level options as a single item
    config = DumpsterConfig.model_validate(raw)
    outputs.append(
        _write_dump(root_path=root_path, config=config, contents_override=contents)
    )
    return outputs
