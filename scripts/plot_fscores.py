#!/usr/bin/env python
# coding: utf-8

import os
import time
from datetime import datetime

import mltk
import pandas as pd
import requests
from matplotlib import pyplot as plt

server = 'http://mlserver.ipwx.me:7980'
client = mltk.MLStorageClient(server)
docs = client.query(limit=10)
URLS = [
    f'{server}/{e["id"]}'
    for e in docs
    if e['status'] == 'RUNNING'
]
print(URLS)


def update_results():
    for url in list(URLS):
        update_result(url)


def update_result(url):
    eid = url.rstrip('/').split('/')[-1]
    res_list = requests.get(f'{server}/v1/_listdir/{eid}/result/test-anomaly').json()
    res_list.sort(key=lambda item: item['mtime'])
    data = []

    for item in res_list:
        if item['name'].endswith('.json'):
            epoch = item['name'][:-5]
            try:
                epoch = int(epoch)
            except ValueError:
                pass

            res_path = f'{server}/v1/_getfile/{eid}/{item["path"]}'
            res_content = requests.get(res_path).json()

            row = dict(res_content)
            if isinstance(epoch, int):
                row['epoch'] = epoch
            elif epoch == 'final':
                row['epoch'] = data[-1]['epoch'] + 10
            else:
                continue
            data.append(row)

    old_doc = client.get(eid)
    if len(data) > 0:
        old_doc = client.get(eid)
        old_result = old_doc['result']
        old_result.update(data[-1])
        client.update(eid, {'result': old_result})

        data = pd.DataFrame(data)
        data = data.set_index('epoch')
        data[['best_fscore', 'best_fscore_drop', 'best_fscore_latency']].plot(figsize=(12, 6))
        plt.grid()
        figure_dir = os.path.join(old_doc['storage_dir'], 'figures')
        os.makedirs(figure_dir, exist_ok=True)
        plt.savefig(os.path.join(figure_dir, 'fscore.jpg'))
        plt.close()

    if old_doc['status'] != 'RUNNING':
        URLS.remove(url)

    data = pd.DataFrame(data)


while URLS:
    update_results()
    print(f'[{datetime.now():%Y-%m-%d %H:%M:%S}] {len(URLS)} remains ...')
    time.sleep(30)
