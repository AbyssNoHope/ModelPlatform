import pandas as pd
import numpy as np
from tqdm import tqdm

df_list = []
path_list = []

for i in [1, 2, 3, 4, 5, 6]:
    for svc in ['r1apssvc', 
    'r1buyingsvcio', 'r1crlstngsv7', 
    'r1icachesrv', 'r1svls16', 'r1adrbksvc', 'r1adrmgtsvc12', 
    'r1oauthclnt', 'r1fmpsvc2', 'r1mpmtsvc', 'r1itmsvcio', 'r1viappsvc12']:
        path_list.append(f'/cpu-v-xz21/multisvc2l/{i}/{svc}/2021-12-05.csv.xz')

print('Reading from file...')
with tqdm(path_list) as t:
    for path in t:
        t.set_description(path)

        df_list.append(pd.read_csv(path, engine='c'))

print('Processing...')
out_data = pd.concat(df_list, ignore_index=True, sort=False)

print('Writing...')
out_data.to_csv('new/multisvc2l/2021-12-05.csv', index=False)
