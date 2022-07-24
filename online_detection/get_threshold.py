from pprint import pprint

import click
import mltk
from numpy import float32
import tensorkit as tk
import time
import csv
import torch
from tensorkit import tensor as T

from tracegnn.data import *
from tracegnn.models.vgae.dataset import TraceGraphDataStream
from tracegnn.models.vgae.evaluation import *
from tracegnn.models.vgae.graph_utils import *
from online_detection.load_model import *
from tracegnn.models.vgae.types import TraceGraphBatch
from tracegnn.utils import *
from tracegnn.visualize import *

from tqdm import tqdm

class Params:
    batch_size = 64
    #训练数据存放位置
    root_dir = 'data/service2_new/processed'
    dataset = 'service2'
    #模型存放位置
    model_path = 'results/train_2022-07-18_20-44-27_221/models/final.pt'
    clip_nll = float(100_000)
    use_biased: bool = True
    #csv file
    input_path = 'online_test/detection_data/detection_trace.csv'
    data_names = ['test', 'test-drop-anomaly4', 'test-latency-anomaly4']

def get_threshold():
        # load the dataset
        val_db, _ = open_trace_graph_db(
            './data/service2/processed',
            names=['val']
        )
        db, id_manager = open_trace_graph_db(
            './data/service2/processed',
            names=Params.data_names
        )
        latency_range = TraceGraphLatencyRangeFile(
            id_manager.root_dir,
            require_exists=True,
        )

        val_stream = TraceGraphDataStream(
            val_db, id_manager=id_manager, batch_size=Params.batch_size,
            shuffle=False, skip_incomplete=False,
        )
        
        vae = load_model(
            model_path=Params.model_path,
            id_manager=id_manager,
            strict=False,
            extra_args=[]
        )
        
        vae.eval()
        print('load success!')
        mltk.print_config(vae.config, title='Model Config')
        vae = vae.to(T.current_device())
        
        def validate():
            nll_score = []
            def val_step(trace_graphs):
                with tk.layers.scoped_eval_mode(vae), T.no_grad():
                    G = TraceGraphBatch(
                        id_manager=id_manager,
                        latency_range=latency_range,
                        trace_graphs=trace_graphs,
                    )
                    chain = vae.q(G, n_z=10).chain(
                        vae.p,
                        G=G,
                        n_z = 10,
                        latent_axis=0,
                        use_biased = True
                    )
                    nll = -chain.vi.evaluation.is_loglikelihood()
                    nll_temp = []

                    index = 0
                    for cnt in list(G.dgl_batch.batch_num_nodes()):
                        nll_temp.append(torch.mean(nll[index:index+cnt]).item())
                        index += cnt
                    
                    clip_limit = T.float_scalar(Params.clip_nll)
                    nll = torch.tensor(nll_temp, device=nll.device, dtype=torch.float)
                    nll = T.where(nll < clip_limit, nll, clip_limit)
                    for score in nll:
                        nll_score.append(score)

            for [trace_graphs] in tqdm(val_stream, desc='Validation', total=val_stream.batch_count):
                val_step(trace_graphs)
        
            return nll_score
        
        nll_score = validate()
        float_nll_score = []
        for score in nll_score:
            float_nll_score.append(float(score))
        
        float_nll_score.sort()
        threshold = float_nll_score[int(len(float_nll_score)*0.995)]
        # print("threshold:",threshold)
        # with open('threshold', 'w') as f:
        #     f.write(str(threshold))
        return threshold

if __name__ == '__main__':
    get_threshold()