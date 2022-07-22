#!/bin/bash

SERVICE="$1"
if [[ "${SERVICE}" == "" ]]; then
  echo "make-train-test.sh service-name"
  exit -1
fi

if [[ -d "/srv/data/tracegnn" ]]; then
  DATA_ROOT="${DATA_ROOT:-/srv/data/tracegnn}"
else
  DATA_ROOT="${DATA_ROOT:-$(pwd)/data}"
fi
DATA_ROOT="${DATA_ROOT}/${SERVICE}"

echo "DATA_ROOT: ${DATA_ROOT}"

# start to process data
set -e

# do the jobs
ORIGIN_DIR="${ORIGIN_DIR:-./data}/${SERVICE}/origin"
echo "ORIGIN_DIR: ${ORIGIN_DIR}"

PROCESSED_DIR="${DATA_ROOT}/processed"
echo "PROCESSED_DIR: ${PROCESSED_DIR}"

python3 -m tracegnn.cli.data_process make-train-test \
    -F \
    -M \
    -i \
    "${ORIGIN_DIR}" \
    -o \
    "${PROCESSED_DIR}" \
    --train-size=100000 \
    --test-size=50000 \
    --max-root-latency="${MAX_ROOT_LATENCY}"

python3 -m tracegnn.cli.data_process make-synthetic-test \
    -F \
    -i \
    "${PROCESSED_DIR}/test" \
    -o \
    "${PROCESSED_DIR}/test-drop-anomaly" \
    --test-size=2500 \
    --drop-ratio 0.2 0.5

python3 -m tracegnn.cli.data_process make-synthetic-test \
    -F \
    -i \
    "${PROCESSED_DIR}/test" \
    -o \
    "${PROCESSED_DIR}/test-latency-anomaly" \
    --test-size=2500 \
    --latency-ratio 0.2 0.5
