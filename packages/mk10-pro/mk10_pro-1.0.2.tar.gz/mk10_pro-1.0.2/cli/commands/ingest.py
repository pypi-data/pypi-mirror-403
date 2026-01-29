# SPDX-License-Identifier: MIT
"""Ingest command."""

import click
from pathlib import Path
from typing import List
import yaml

from engine.util.fs import content_hash, get_file_info
from engine.util.time import utc_now, to_iso8601


@click.command()
@click.option("--source", required=True, type=click.Path(exists=True), help="Source directory or file")
@click.option("--output", default="ingest_manifest.yaml", help="Output manifest file")
@click.option("--workspace", default=".workspace", help="Workspace directory")
def ingest(source: str, output: str, workspace: str):
    """Ingest source assets and create manifest."""
    source_path = Path(source)
    workspace_path = Path(workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    click.echo(f"Ingesting assets from: {source_path}")
    
    assets: List[dict] = []
    
    if source_path.is_file():
        files = [source_path]
    else:
        files = list(source_path.rglob("*"))
        files = [f for f in files if f.is_file()]
    
    for file_path in files:
        try:
            info = get_file_info(file_path)
            content_addr = f"{info['hash']}{file_path.suffix}"
            
            asset = {
                "content_address": content_addr,
                "path": str(file_path),
                "hash": info["hash"],
                "size": info["size"],
                "metadata": {
                    "mtime": info["mtime"],
                },
            }
            assets.append(asset)
            click.echo(f"  Ingested: {file_path.name} ({info['size']} bytes)")
        except Exception as e:
            click.echo(f"  Error ingesting {file_path}: {e}", err=True)
    
    manifest = {
        "ingest_timestamp": to_iso8601(utc_now()),
        "source": str(source_path),
        "assets": assets,
        "total_assets": len(assets),
    }
    
    manifest_path = workspace_path / output
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False)
    
    click.echo(f"\nIngest complete: {len(assets)} assets")
    click.echo(f"Manifest saved to: {manifest_path}")

