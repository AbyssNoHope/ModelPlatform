#!/usr/bin/env python

import os
import socket
import sys

from scripts.utils import *


if __name__ == '__main__':
    script_dir = os.path.split(os.path.abspath(__file__))[0]
    source_dir = os.path.realpath(os.path.join(script_dir, '../data'))
    dest_dir = DATA_DIR
    hostname = socket.gethostname()

    if not hostname.endswith('.cluster.peidan.me'):
        print('Only work at lab cluster.', file=sys.stderr)
        exit(1)

    if hostname == 'cpu1.cluster.peidan.me':
        source_dir, dest_dir = dest_dir, source_dir

    source_dir = source_dir.rstrip('/')
    dest_dir = dest_dir.rstrip('/')
    shell([
        'rsync', '-avR', '--delete',
        source_dir + '/./',
        dest_dir,
    ])
    # shell(['tree', dest_dir])
