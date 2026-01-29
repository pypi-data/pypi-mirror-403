# SPDX-License-Identifier: MIT
"""Verify command."""

import click
from pathlib import Path

from mtb.verify import verify_mtb


@click.command()
@click.option("--mtb", required=True, type=click.Path(exists=True), help="MTB file path")
def verify(mtb: str):
    """Verify Master Truth Bundle."""
    mtb_path = Path(mtb)
    
    click.echo(f"Verifying MTB: {mtb_path}")
    
    results = verify_mtb(mtb_path)
    
    if results["valid"]:
        click.echo("✓ MTB is valid")
        if results["warnings"]:
            click.echo("\nWarnings:")
            for warning in results["warnings"]:
                click.echo(f"  - {warning}")
    else:
        click.echo("✗ MTB is invalid")
        click.echo("\nErrors:")
        for error in results["errors"]:
            click.echo(f"  - {error}")
        raise click.Abort()

