"""
Query subject's information
"""
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import click

from connecticity.managers.subjects.process_subjects import (
    SubjectsManager,
)


@click.command()
@click.argument("base_dir", type=click.Path(exists=True))
@click.option("-destination", "--destination", type=click.Path(), default=None)
@click.option("-bids_dir", "--bids_dir", type=click.Path(), default=None)
def main(base_dir: Path, destination: Path = None, bids_dir: Path = None):
    manager = SubjectsManager(base_dir, destination, bids_dir)
    manager.query_subjects()


if __name__ == "__main__":
    main()
