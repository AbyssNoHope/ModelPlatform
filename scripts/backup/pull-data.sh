#!/bin/bash

set -e

mkdir -p /srv/data/tracegnn
rsync -avR gpu1:/srv/data/tracegnn/./* /srv/data/tracegnn/
