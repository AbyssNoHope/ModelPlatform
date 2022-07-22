#!/usr/bin/env python

import os

import click

from scripts.utils import *


@click.command()
def main():
    for name in DATASETS:
        data_dir = os.path.join(DATA_DIR, name)
        shell(
            f'python3 -m tracegnn.cli.data_process downgrade-protocol '
            f'-i "{data_dir}/processed"'
        )


if __name__ == '__main__':
    main()
