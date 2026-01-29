"""Upload dbt artifacts to Colibri Pro."""

import base64
import gzip
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from rich.console import Console

from . import __version__
from .config import Config

console = Console()


class UploadError(Exception):
    """Error during artifact upload."""


def get_git_info() -> dict:
    """Get git commit information if available.

    Returns:
        Dictionary with git metadata, or empty dict if not in a git repo
    """
    try:
        # Get commit hash
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        # Get branch name
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        return {
            "git_commit": commit,
            "git_branch": branch,
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not in a git repo or git not available
        return {}


def find_artifacts(target_dir: Path) -> tuple[Path, Path]:
    """Find manifest.json and catalog.json in the target directory.

    Args:
        target_dir: Path to dbt target directory

    Returns:
        Tuple of (manifest_path, catalog_path)

    Raises:
        UploadError: If required files are not found
    """
    manifest_path = target_dir / "manifest.json"
    catalog_path = target_dir / "catalog.json"

    if not manifest_path.exists():
        raise UploadError(f"manifest.json not found in {target_dir}")

    if not catalog_path.exists():
        raise UploadError(f"catalog.json not found in {target_dir}")

    return manifest_path, catalog_path


def compress_and_encode(file_path: Path) -> str:
    """Compress and base64 encode a file.

    Args:
        file_path: Path to the file

    Returns:
        Base64 encoded gzipped content
    """
    with open(file_path, "rb") as f:
        content = f.read()
        compressed = gzip.compress(content, compresslevel=6)
        return base64.b64encode(compressed).decode("utf-8")


def upload_artifacts(
    config: Config,
    target_dir: Path,
    version_id: str | None = None,
) -> str:
    """Upload dbt artifacts to Colibri Pro API.

    Args:
        config: CLI configuration
        target_dir: Path to dbt target directory
        version_id: Optional version identifier (defaults to timestamp-based UUID)

    Returns:
        The version_id used for the upload

    Raises:
        UploadError: If upload fails
    """
    # Generate version ID if not provided
    if not version_id:
        version_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    console.print(f"[bold blue]Uploading artifacts for version:[/] {version_id}")

    # Find artifacts
    manifest_path, catalog_path = find_artifacts(target_dir)

    console.print(f"  [dim]Found manifest.json:[/] {manifest_path}")
    console.print(f"  [dim]Found catalog.json:[/] {catalog_path}")

    # Compress and encode artifacts
    console.print("  [dim]Compressing artifacts...[/]")
    try:
        manifest_encoded = compress_and_encode(manifest_path)
        catalog_encoded = compress_and_encode(catalog_path)
    except Exception as e:
        raise UploadError(f"Failed to compress artifacts: {e}")

    console.print("  [green]✓[/] Artifacts compressed and encoded")

    # Prepare metadata
    metadata = {
        "colibri_cli_version": __version__,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    # Add git info if available
    git_info = get_git_info()
    if git_info:
        metadata.update(git_info)
        console.print(f"  [dim]Git commit:[/] {git_info.get('git_commit', 'N/A')[:8]}")
        console.print(f"  [dim]Git branch:[/] {git_info.get('git_branch', 'N/A')}")

    # Prepare request payload
    payload = {
        "project_id": config.project_id,
        "version_id": version_id,
        "manifest": manifest_encoded,
        "catalog": catalog_encoded,
        "metadata": metadata,
    }

    # Upload to API
    api_url = f"{config.api_url.rstrip('/')}/upload-artifacts"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    console.print(f"  [dim]Uploading to:[/] {api_url}")

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=60,
        )

        # Check for errors
        if response.status_code != 200:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", error_data.get("error", str(error_data)))
            except Exception:
                error_detail = response.text or f"HTTP {response.status_code}"

            raise UploadError(f"Upload failed: {error_detail}")

        result = response.json()

    except requests.exceptions.RequestException as e:
        raise UploadError(f"Network error: {e}")
    except Exception as e:
        raise UploadError(f"Failed to upload: {e}")

    console.print(f"  [green]✓[/] Upload complete")

    console.print(f"\n[bold green]✓ Success![/]")
    console.print(f"  Version ID: {result.get('version_id', version_id)}")
    console.print(f"  Job ID: {result.get('job_id', 'N/A')}")
    console.print(f"  Status: {result.get('status', 'uploaded')}")

    return version_id




