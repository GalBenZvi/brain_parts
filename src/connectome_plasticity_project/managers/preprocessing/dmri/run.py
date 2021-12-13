"""
Query subject's information
"""
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import click

from connectome_plasticity_project.managers.preprocessing.dmri.dmri import (
    DmriManager,
)


@click.command()
@click.argument("bids_dir", type=click.Path(exists=True))
@click.option("-destination", "--destination", type=click.Path(), default=None)
@click.option("-max_total", "--max_total", type=int, default=None)
def main(bids_dir: Path, destination: Path = None, max_total: int = None):
    manager = DmriManager(bids_dir, destination)
    manager.run(max_total)


if __name__ == "__main__":
    main()
