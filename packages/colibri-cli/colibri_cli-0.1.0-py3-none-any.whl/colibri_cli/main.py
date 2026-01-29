"""Colibri CLI - Main entry point."""

from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .config import Config
from .upload import UploadError, upload_artifacts

console = Console()


@click.group()
@click.version_option(version=__version__)
def cli():
    """Colibri Pro CLI - Upload dbt artifacts to Colibri Pro."""
    pass


@cli.command()
@click.option(
    "--target-dir",
    "-t",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default="target",
    help="Path to dbt target directory (default: ./target)",
)
@click.option(
    "--version-id",
    "-v",
    type=str,
    default=None,
    help="Custom version identifier (default: auto-generated timestamp)",
)
def upload(target_dir: Path, version_id: str | None):
    """Upload dbt manifest and catalog to Colibri Pro.

    This command uploads your dbt artifacts (manifest.json and catalog.json)
    to Colibri Pro for lineage analysis. The artifacts are compressed, encoded,
    and sent to the API along with metadata including git commit information.

    Required environment variables:
        COLIBRI_API_URL: Your Colibri Pro API URL
        COLIBRI_API_KEY: Your API key
        COLIBRI_PROJECT_ID: Your project ID
    """
    try:
        # Load configuration
        config = Config.from_env()

        # Upload artifacts
        upload_artifacts(config, target_dir, version_id)

    except ValueError as e:
        console.print(f"[bold red]Configuration error:[/] {e}")
        raise SystemExit(1)

    except UploadError as e:
        console.print(f"[bold red]Upload error:[/] {e}")
        raise SystemExit(1)

    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/] {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    cli()




