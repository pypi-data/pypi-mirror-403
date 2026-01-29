"""Template update functionality for tdd-llm."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import httpx

from .paths import get_templates_cache_dir

# Constants
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/mxdumas/tdd-llm-workflow/main"
TEMPLATES_PATH = "src/tdd_llm/templates"
MANIFEST_URL = f"{GITHUB_RAW_BASE}/{TEMPLATES_PATH}/manifest.json"
# Cache-busting headers to avoid stale CDN responses
CACHE_BUSTING_HEADERS = {"Cache-Control": "no-cache", "Pragma": "no-cache"}


@dataclass
class Manifest:
    """Template manifest from repository."""

    version: str
    templates: dict[str, str]  # path -> checksum

    @classmethod
    def from_json(cls, data: dict) -> Manifest:
        """Create manifest from JSON data."""
        return cls(
            version=data.get("version", "0.0.0"),
            templates=data.get("templates", {}),
        )

    def to_json(self) -> dict:
        """Convert manifest to JSON-serializable dict."""
        return {"version": self.version, "templates": self.templates}


@dataclass
class UpdateResult:
    """Result of an update operation."""

    status: Literal["updated", "up_to_date", "error"]
    version: str | None = None
    previous_version: str | None = None
    files_updated: list[str] = field(default_factory=list)
    files_unchanged: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def get_local_manifest() -> Manifest | None:
    """Load local manifest if it exists."""
    manifest_path = get_templates_cache_dir() / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return Manifest.from_json(json.load(f))
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def _fetch_remote_manifest(client: httpx.Client) -> Manifest:
    """Fetch manifest from GitHub."""
    response = client.get(MANIFEST_URL, headers=CACHE_BUSTING_HEADERS)
    response.raise_for_status()
    return Manifest.from_json(response.json())


def _download_file(client: httpx.Client, relative_path: str, dest: Path) -> str:
    """Download a single file and return its checksum."""
    url = f"{GITHUB_RAW_BASE}/{TEMPLATES_PATH}/{relative_path}"
    response = client.get(url, headers=CACHE_BUSTING_HEADERS)
    response.raise_for_status()

    content = response.content
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)

    return hashlib.sha256(content).hexdigest()


def _verify_checksum(file_path: Path, expected: str) -> bool:
    """Verify file checksum matches expected."""
    if not file_path.exists():
        return False
    content = file_path.read_bytes()
    actual = hashlib.sha256(content).hexdigest()
    return actual == expected


def update_templates(
    force: bool = False,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> UpdateResult:
    """Update templates from GitHub.

    Args:
        force: If True, re-download all files regardless of version.
        progress_callback: Optional callback(current, total, filename) for progress.

    Returns:
        UpdateResult with details of what was done.
    """
    result = UpdateResult(status="error")

    try:
        # Use fresh transport to avoid stale CDN edge connections
        transport = httpx.HTTPTransport(retries=2)
        with httpx.Client(timeout=30.0, follow_redirects=True, transport=transport) as client:
            # Fetch remote manifest
            remote_manifest = _fetch_remote_manifest(client)
            result.version = remote_manifest.version

            # Check local manifest
            local_manifest = get_local_manifest()
            result.previous_version = local_manifest.version if local_manifest else None

            # Check if update needed
            if not force and local_manifest:
                if local_manifest.version == remote_manifest.version:
                    result.status = "up_to_date"
                    return result

            # Download to temp directory first (atomic update)
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                files_to_download = remote_manifest.templates
                total = len(files_to_download)

                for idx, (rel_path, expected_checksum) in enumerate(files_to_download.items()):
                    if progress_callback:
                        progress_callback(idx + 1, total, rel_path)

                    dest = temp_path / rel_path

                    # Check if we can skip (same checksum in cache)
                    cache_file = get_templates_cache_dir() / rel_path
                    if not force and cache_file.exists():
                        if _verify_checksum(cache_file, expected_checksum):
                            result.files_unchanged.append(rel_path)
                            # Copy existing file to temp
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(cache_file, dest)
                            continue

                    # Download file
                    actual_checksum = _download_file(client, rel_path, dest)

                    # Verify checksum
                    if actual_checksum != expected_checksum:
                        result.errors.append(
                            f"Checksum mismatch for {rel_path}: "
                            f"expected {expected_checksum[:8]}..., got {actual_checksum[:8]}..."
                        )
                        result.status = "error"
                        return result

                    result.files_updated.append(rel_path)

                # Save manifest to temp
                manifest_dest = temp_path / "manifest.json"
                with open(manifest_dest, "w", encoding="utf-8") as f:
                    json.dump(remote_manifest.to_json(), f, indent=2)

                # Atomic replace: remove old cache and move new
                cache_dir = get_templates_cache_dir()
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                cache_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(temp_path, cache_dir)

            result.status = "updated"

    except httpx.HTTPStatusError as e:
        result.errors.append(f"HTTP error: {e.response.status_code} for {e.request.url}")
    except httpx.ConnectError:
        result.errors.append("Network error: Could not connect to GitHub")
    except httpx.TimeoutException:
        result.errors.append("Network error: Request timed out")
    except PermissionError as e:
        result.errors.append(f"Permission error: Cannot write to cache directory: {e}")
    except OSError as e:
        result.errors.append(f"File system error: {e}")

    return result
