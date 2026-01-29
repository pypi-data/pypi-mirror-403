# SPDX-License-Identifier: MIT
"""MK10-PRO CLI main entry point."""

import click
from pathlib import Path

from cli.commands.ingest import ingest
from cli.commands.execute import execute
from cli.commands.promote import promote
from cli.commands.verify import verify


@click.group()
@click.version_option(version="1.0.0")
def main():
    """MK10-PRO - Deterministic Pre-Delivery Truth Infrastructure."""
    pass


main.add_command(ingest)
main.add_command(execute)
main.add_command(promote)
main.add_command(verify)


if __name__ == "__main__":
    main()

