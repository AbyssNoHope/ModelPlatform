#!/usr/bin/env python

import os

from scripts.utils import *


if __name__ == '__main__':
    cnt = []

    for dataset in ['service2l']:
        data_dir = os.path.join(DATA_DIR, dataset)
        figure_dir = os.path.join(
            os.path.split(os.path.abspath(__file__))[0],
            f'../paper-data/figures/{dataset}'
        )
        if not os.path.isdir(figure_dir):
            os.makedirs(figure_dir, exist_ok=True)

        cnt.append(f'## {dataset}\n')
        for tag in ('origin', 'processed',):
            path = os.path.join(data_dir, tag)
            if os.path.exists(path):
                cnt.append(f'### {tag.capitalize()}\n')
                tag_figure_dir = os.path.join(figure_dir, tag)
                os.makedirs(tag_figure_dir, exist_ok=True)

                # data-hist
                args = (
                    f'python3 -m tracegnn.cli.data_stat data-hist '
                    f'-i "{data_dir}/{tag}" '
                )
                if tag == 'processed':
                    args += '--names train,test '
                args += (
                    f'--node-count-hist-out={os.path.join(tag_figure_dir, "node_count.jpg")} '
                    f'--max-depth-hist-out={os.path.join(tag_figure_dir, "max_depth.jpg")} '
                    f'--root-latency-hist-out={os.path.join(tag_figure_dir, "root_latency.jpg")}'
                )
                output = shell(args, get_output=True)
                # for c in '█▊':
                #     output = output.replace(c, '')
                cnt.append(f'\n```\n{output}\n```\n\n')

                # latency-hist
                args = (
                    f'python3 -m tracegnn.cli.data_stat latency-hist '
                    f'-i "{data_dir}/{tag}" '
                )
                if tag == 'processed':
                    args += '--names train,test '
                args += (
                    f'--output-file={os.path.join(tag_figure_dir, "latency_hist.jpg")} '
                )
                output = shell(args, get_output=True)

                # # latency-hist on anomaly
                # for suffix in ['', '2']:
                #     args = (
                #         f'python3 -m tracegnn.cli.data_stat latency-hist '
                #         f'-i "{data_dir}/{tag}" '
                #     )
                #     if tag == 'processed':
                #         args += f'--names test-latency-anomaly{suffix} '
                #     args += (
                #         f'--output-file={os.path.join(figure_dir, tag, f"latency_hist-anomaly{suffix}.jpg")} '
                #     )
                #     output = shell(args, get_output=True)

    print('')
    print('\n'.join(cnt))
