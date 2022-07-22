#!/bin/bash

if [[ "${SERVICE}" == "" ]]; then
  echo "SERVICE=service-name gpu-train.sh"
  exit -1
fi

if [[ -d "/srv/data/tracegnn" ]]; then
  DATA_ROOT="${DATA_ROOT:-/srv/data/tracegnn}"
else
  DATA_ROOT="${DATA_ROOT:-$(pwd)/data}"
fi
DATA_ROOT="${DATA_ROOT}/${SERVICE}"
echo DATA_ROOT: "${DATA_ROOT}"

exec mlrun --tensorboard -- \
  python3 -m tracegnn.models.trace_vae.train \
    --device="cuda:0" \
    --dataset.root_dir="${DATA_ROOT}/processed" \
    "$@"
