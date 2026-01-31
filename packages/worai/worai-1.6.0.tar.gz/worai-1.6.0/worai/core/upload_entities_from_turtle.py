"""Upload Turtle files to WordLift /entities with resume support."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from tqdm import tqdm

import wordlift_client
from wordlift_client import ApiClient, Configuration
from wordlift_client.exceptions import ApiException

DEFAULT_EXTENSIONS = {".ttl", ".turtle"}


@dataclass
class UploadOptions:
    folder: Path
    recursive: bool = False
    limit: int = 0
    state_file: Path | None = None
    base_url: str = "https://api.wordlift.io"
    api_key: str | None = None


def gather_files(folder: Path, recursive: bool, extensions: Set[str]) -> List[Path]:
    candidates = folder.rglob("*") if recursive else folder.glob("*")
    files = [p for p in candidates if p.is_file() and p.suffix.lower() in extensions]
    return sorted(files)


def load_state(path: Path) -> Dict:
    if not path.exists():
        return {"processed": [], "failed": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"processed": [], "failed": {}}
    if not isinstance(data, dict):
        return {"processed": [], "failed": {}}
    data.setdefault("processed", [])
    data.setdefault("failed", {})
    return data


def save_state(path: Path, state: Dict) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def relpath(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


async def upload_entities(
    folder: Path,
    files: List[Path],
    api_key: str,
    base_url: str,
    state_path: Path,
) -> int:
    state = load_state(state_path)
    processed_set = set(state.get("processed", []))
    failed_map = state.get("failed", {})

    config = Configuration(host=base_url)
    config.api_key["ApiKey"] = api_key
    config.api_key_prefix["ApiKey"] = "Key"

    total = len(files)
    skipped = 0
    success = 0
    failed = 0

    async with ApiClient(config) as api_client:
        api = wordlift_client.EntitiesApi(api_client)
        for path in tqdm(files, total=total, unit="file", desc="Uploading"):
            rel = relpath(path, folder)
            if rel in processed_set:
                skipped += 1
                continue
            try:
                content = path.read_text(encoding="utf-8")
                if not content.strip():
                    raise ValueError("file is empty")
                await api.create_or_update_entities(content, _content_type="text/turtle")
            except (OSError, ValueError, ApiException) as exc:
                failed += 1
                failed_map[rel] = str(exc)
                print(f"FAILED: {rel} -> {exc}")
            else:
                success += 1
                processed_set.add(rel)
                if rel in failed_map:
                    failed_map.pop(rel, None)
            state["processed"] = sorted(processed_set)
            state["failed"] = failed_map
            save_state(state_path, state)

    print(
        f"Done. total={total} success={success} failed={failed} skipped={skipped} "
        f"state={state_path}"
    )
    return 0 if failed == 0 else 2


def run(options: UploadOptions) -> int:
    folder = options.folder
    state_path = options.state_file or (folder / ".entities_upload_state.json")

    files = gather_files(folder, options.recursive, DEFAULT_EXTENSIONS)
    if not files:
        raise RuntimeError(f"No Turtle files found in {folder}")

    state = load_state(state_path)
    processed_set = set(state.get("processed", []))
    to_process = [p for p in files if relpath(p, folder) not in processed_set]

    if options.limit and options.limit > 0:
        to_process = to_process[: options.limit]

    if not to_process:
        print("Nothing to do; all files are already processed.")
        return 0

    return asyncio.run(upload_entities(folder, to_process, options.api_key, options.base_url, state_path))
