#!/usr/bin/env python3

import sys

import click

from scripts.utils import run_parallel_with_gpus


@click.command()
@click.option('-g', '--gpu', 'gpus', required=True, default=None)
@click.option('-k', '--job-per-gpu', type=int, default=2)
@click.option('-M', '--model', 'models', required=False, multiple=True)
@click.option('-f', '--model-file', required=False, default=None)
def main(gpus, job_per_gpu, models, model_file):
    # parse the gpus
    gpu_list = []
    for g in gpus.split(','):
        g = g.strip()
        if '-' in g:
            l, r = g.split('-')
            l = int(l)
            r = int(r)
            for i in range(l, r + 1):
                gpu_list.append(i)
        elif g:
            gpu_list.append(int(g))

    gpu_list = sorted(set(gpu_list))
    gpu_list = list(sum([[g] * job_per_gpu for g in gpu_list], []))

    # load the models
    models = models or []
    if model_file:
        with open(model_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    models.append(line)
    if not models:
        print(f'No model is specified.', file=sys.stderr)
        exit(-1)

    # generate the arguments
    arg_list = []

    for m in models:
        arg_list.extend([
            # ordinary test
            (lambda gpu, model=m: [
                './scripts/test.py', '-g', gpu,
                '-M', model,
                '--infer-threshold',
                '--data4',
                '--use-std-limit',
                '--std-limit-global',
                '-t', 'main,std-limit-global',
            ]),
            # no biased, no log-prob-weight (NLL)
            (lambda gpu, model=m: [
                './scripts/test.py', '-g', gpu,
                '-M', model,
                '--infer-threshold',
                '--data4',
                '--no-biased',
                '--no-latency-log-prob-weight',
                '-t', 'main,no-log-prob-weight',
            ]),
            # no biased, std-limit-global-only (StdLimit)
            (lambda gpu, model=m: [
                './scripts/test.py', '-g', gpu,
                '-M', model,
                '--infer-threshold',
                '--data4',
                '--no-biased',
                '--no-latency-log-prob-weight',
                '--use-std-limit',
                '--std-limit-global',
                '-t', 'main,std-limit-global-only',
            ]),
            # log-prob-weight-only (NCNorm)
            (lambda gpu, model=m: [
                './scripts/test.py', '-g', gpu,
                '-M', model,
                '--infer-threshold',
                '--data4',
                '--no-biased',
                '-t', 'main,log-prob-weight-only',
            ]),
            # struct biased, no log-prob-weight (BCScale)
            (lambda gpu, model=m: [
                './scripts/test.py', '-g', gpu,
                '-M', model,
                '--infer-threshold',
                '--data4',
                '--no-latency-biased',
                '--no-latency-log-prob-weight',
                '-t', 'main,struct-biased',
            ]),
        ])

    # now run the tests
    run_parallel_with_gpus(arg_list, gpu_list)


if __name__ == '__main__':
    main()
