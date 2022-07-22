#!/usr/bin/env python

import os

import click

from scripts.utils import *
from data_process.process_original_data import gen_csv

MAX_ROOT_LATENCY = {
    'service2': 5000000
}


@click.command()
@click.option('-F', '--force-generate', is_flag=True, default=False)
@click.option('-f', '--filepath', type = str, help='the original file path of data')
@click.option('-n', '--names', multiple=True, default=None)
def main(force_generate, filepath,names):
    # os.chdir('/home/liuheng/vgae')
    force_flag = '-F' if force_generate else ''
    cnt = []
    
    def sh(args):
        o = shell(args, get_output=True).strip()
        if o:
            cnt.append(f'```\n{o}\n```')

    if names:
        names = sum([n.split(',') for n in names], [])
    
    print('names: ', names)
    print('DATASETS: ',DATASETS)
    for name in DATASETS:
        if names and (name not in names):
            print('continue success!')
            continue
        
        print('DATA_DIR: ', DATA_DIR)
        data_dir = os.path.join(DATA_DIR, name)
        print('data_dir: ',data_dir)
        max_root_latency = MAX_ROOT_LATENCY[name]
        cnt.append(f'## {name}\n')

        if True:
            # the origin data
            if not os.path.isdir(data_dir + '/origin'):
                cnt.append(f'### csv-to-db\n')
                sh(
                    f'python3 -m tracegnn.cli.data_process csv-to-db '
                    f'-i "{data_dir}/raw" '
                    f'-o "{data_dir}/origin"'
                )
                cnt.append('\n\n')

            # make train / val / test
            if not os.path.isdir(data_dir + '/processed') or force_generate:
                cnt.append(f'### make-train-test\n')
                sh(
                    f'python3 -m tracegnn.cli.data_process make-train-test {force_flag} -M '
                    f'-i "{data_dir}/origin" '
                    f'-o "{data_dir}/processed" '
                    f'--train-size=250000 '
                    f'--val-size=20000 '
                    f'--test-size=5000 '
                    f'--max-root-latency={max_root_latency}'
                )
                cnt.append('\n\n')

            # make latency range
            sh(
                f'python3 -m tracegnn.cli.data_process make-latency-range {force_flag} '
                f'-i "{data_dir}/processed" '
                f'--names train,val'
            )

        # see this
        if True:
            cnt.append(f'### make-drop-anomaly4\n')
            sh(
                f'python3 -m tracegnn.cli.data_process make-synthetic-test {force_flag} '
                f'-i "{data_dir}/processed/test" '
                f'-o "{data_dir}/processed/test-drop-anomaly4" '
                f'--test-size=500 '
                f'--drop-ratio 0.1 0.5 '
            )
            cnt.append('\n\n')

            cnt.append(f'### make-latency-anomaly4\n')
            sh(
                f'python3 -m tracegnn.cli.data_process make-synthetic-test {force_flag} '
                f'-i "{data_dir}/processed/test" '
                f'-o "{data_dir}/processed/test-latency-anomaly4" '
                f'--test-size=500 '
                f'--avg-as-whole '
                f'--latency-ratio 0.1 0.5 '
                f'--latency-delta-np99 2.0 10.0 '
                f'--latency-p99-min 1'
            )
            cnt.append('\n\n')

    print('\n'.join(cnt))


if __name__ == '__main__':
    main()
