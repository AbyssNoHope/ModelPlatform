#!/usr/bin/env python
import os
import re
import socket

import click

from scripts.utils import *


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    help_option_names=[],
))
@click.option('-D', '--dataset', required=True)
@click.option('-M', '--model-path', required=True)
@click.option('-C', '--command', required=True)
@click.option('-g', '--gpu', required=False, type=int, default=None)
@click.argument('extra_args', nargs=-1, type=click.UNPROCESSED)
def main(dataset, model_path, command, gpu, extra_args):
    # inspect the device
    if gpu is None:
        hostname = socket.gethostname()
        if re.match(r'^gpu(\d+)\.cluster\.peidan\.me$', hostname):
            raise ValueError(f'You should specify `-g` for using GPU.')
        device = 'cpu'
    else:
        device = 'cuda:0'
        os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu)

    # compose arguments
    args1 = [
        'mlrun',
        '-t', dataset,
        '-t', 'test',
        '-t', command,
    ]
    args2 = [
        '--',
        'python3',
        '-m',
        'tracegnn.models.trace_vae.test',
        command,
        f'--data-dir={DATA_DIR}/{dataset}/processed',
        f'--model-path={model_path}',
        f'--device={device}',
    ]

    if command == 'evaluate-prior':
        args2.extend([
            '--output-file=./results/evaluate_prior.json',
            '--latency-hist-out=./figures/latency-hist.jpg',
        ])

    args2.extend(extra_args)

    # execute the program
    args = args1 + args2
    print(f'> {args}')
    os.execvp(args[0], args)


if __name__ == '__main__':
    main()
