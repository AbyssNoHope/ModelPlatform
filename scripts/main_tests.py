import click

from scripts.utils import run_parallel_with_gpus


@click.command()
@click.option('-g', '--gpu', 'gpus', required=True, default=None)
@click.option('-k', '--job-per-gpu', type=int, default=2)
@click.option('-M', '--model', required=True)
@click.option('-D', '--dataset', required=True)
def main(gpus, job_per_gpu, model, dataset):
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

    # generate the arguments
    arg_list = [
        # ordinary test
        (lambda gpu: [
            './scripts/test.py', '-g', gpu,
            '-D', dataset,
            '-M', model,
            '--infer-threshold',
            '--data4',
            '--use-std-limit',
            '--std-limit-global',
            '-t', 'main,std-limit-global',
        ]),
        # no biased, no log-prob-weight (NLL)
        (lambda gpu: [
            './scripts/test.py', '-g', gpu,
            '-D', dataset,
            '-M', model,
            '--infer-threshold',
            '--data4',
            '--no-biased',
            '--no-latency-log-prob-weight',
            '-t', 'main,no-log-prob-weight',
        ]),
        # no biased, std-limit-global-only (StdLimit)
        (lambda gpu: [
            './scripts/test.py', '-g', gpu,
            '-D', dataset,
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
        (lambda gpu: [
            './scripts/test.py', '-g', gpu,
            '-D', dataset,
            '-M', model,
            '--infer-threshold',
            '--data4',
            '--no-biased',
            '-t', 'main,log-prob-weight-only',
        ]),
        # struct biased, no log-prob-weight (BCScale)
        (lambda gpu: [
            './scripts/test.py', '-g', gpu,
            '-D', dataset,
            '-M', model,
            '--infer-threshold',
            '--data4',
            '--no-latency-biased',
            '--no-latency-log-prob-weight',
            '-t', 'main,struct-biased',
        ]),
    ]

    # now run the tests
    run_parallel_with_gpus(arg_list, gpu_list)


if __name__ == '__main__':
    main()
