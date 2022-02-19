"""
Query subject's information
"""
import warnings
from pathlib import Path
from typing import List

warnings.filterwarnings("ignore")

import click

from connecticity.managers.preprocessing.dmri.dmri import DmriManager


@click.command()
@click.argument("bids_dir", type=click.Path(exists=True))
@click.option("-destination", "--destination", type=click.Path(), default=None)
@click.option("-max_total", "--max_total", type=int, default=None)
@click.option("-participant_label", "--participant_label", multiple=True, default=None)
def main(
    bids_dir: Path,
    destination: Path = None,
    max_total: int = None,
    participant_label: list = None,
):
    if participant_label:
        participant_label = [p for p in participant_label]
    manager = DmriManager(bids_dir, destination)
    manager.run(max_total, participant_label)


if __name__ == "__main__":
    main()
