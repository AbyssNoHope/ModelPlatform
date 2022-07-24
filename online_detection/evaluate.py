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
from online_detection.mergetree import get_complete_trace

from tqdm import tqdm

class Params:
    batch_size = 12
    #训练数据存放位置
    root_dir = './data/service2/processed'
    dataset = 'service2'
    #模型存放位置
    clip_nll = float(100_000)
    use_biased: bool = True
    #csv file
    input_path = 'online_test/detection_data/detection_trace.csv'

def evaluate_nll(input_path, model_name):
    def trace_to_csv(traces):
        operationid = []
        with open('data/service2/processed/latency_range.yml', 'r') as f:
            for span in f:
                operationid.append(span.strip().split(':')[0])
        latency_id = operationid[0:len(operationid):4]
        
        operationid_dict = {}
        with open('data/service2/origin/operation_id.yml', 'r') as f:
            for i in f:
                arr = i.strip().split(':')
                if len(arr) == 2:
                    operationid_dict[arr[0]] = arr[1]
        
        print(operationid_dict)
        with open('online_test/detection_data/detection_trace.csv', 'w') as fp:
            writer = csv.writer(fp)
            writer.writerow(["traceIdHigh","traceIdLow","spanId","parentSpanId","environment","serviceName","colo","hostname","type","status","operationName","startTime","duration","threadId","Tags.Key","Tags.Value","nanosecond","DBhash"])
            for trace in traces:
                trace_csvs = []
                for span in trace:
                    trace_csv = []
                    single = span.strip().split(';')
                    traceIdHigh = single[1][0:16]
                    trace_csv.append(traceIdHigh)
                    traceIdLow = single[1][16:32]
                    trace_csv.append(traceIdLow)
                    spanId = single[2]
                    trace_csv.append(spanId)
                    parentSpanId = single[4]
                    trace_csv.append(parentSpanId)
                    environment = ''
                    trace_csv.append(environment)
                    serviceName = single[9]
                    trace_csv.append(serviceName)
                    colo = ''
                    trace_csv.append(colo)
                    d_hostname = ''
                    trace_csv.append(d_hostname)
                    d_type = ''
                    trace_csv.append(d_type)
                    status = '0'
                    trace_csv.append(status)
                    operationName = single[8]
                    trace_csv.append(operationName)
                    if serviceName + '/' +operationName not in operationid_dict.keys():
                        trace_csvs = []
                        break
                    elif operationid_dict[serviceName + '/' +operationName ].strip() not in latency_id:
                        trace_csvs = []
                        break
                    # 时间戳
                    strmp_time = int(single[6])/1000000
                    timeArray = time.localtime(strmp_time)
                    stTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
                    trace_csv.append(stTime)
                    duration = single[7]
                    trace_csv.append(duration)
                    threadId = 0
                    trace_csv.append(threadId)
                    Tags_Key = '[]'
                    trace_csv.append(Tags_Key)
                    Tags_Value = "[]"
                    trace_csv.append(Tags_Value)
                    startTime = single[6]
                    nanosecond = startTime 
                    trace_csv.append(nanosecond)
                    DBhash = 0
                    trace_csv.append(DBhash)
                    trace_csvs.append(trace_csv)
                    trace_csv = []
                if len(trace_csvs) != 0:
                    for t_csv in trace_csvs:
                        writer.writerow(t_csv)
            
    get_complete_trace(input_path)
    
    with open(input_path+'-merge', 'r') as tn:
        traces = []
        trace = []
        traceid = ""
        for span in tn:
            sp = span.strip()
            si = sp.split(';')
            # 表明trace是空的
            if si[1] != traceid:
                if len(trace)>1:
                    traces.append(trace)
                trace = []
                trace.append(sp)
                traceid = si[1]
            else:
                trace.append(sp) 
                
    trace_to_csv(traces)
    
    model_path = './results/{}/models/final.pt'.format(model_name)
    
    id_manager = TraceGraphIDManager(Params.root_dir)
    latency_range = TraceGraphLatencyRangeFile(Params.root_dir, require_exists=True)

    # load model
    vae = load_model(
            model_path=model_path,
            id_manager=id_manager,
            strict=False,
            extra_args=[]
        )
    vae.eval()
    print('load success!')
    mltk.print_config(vae.config, title='Model Config')
    vae = vae.to(T.current_device())
    
    #input_path: csv_input_path
    df = load_trace_csv(Params.input_path)
    trace_graphs = df_to_trace_graphs(
            df,
            id_manager=id_manager,
            merge_spans=False,
        )
    
    
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
    
    with open('threshold', 'r') as f:
        threshold = float(f.readline())
    
    trace_score_dict = {}
    
    for (graph, score) in zip(trace_graphs, nll):
        if threshold<score:
            # print(graph.trace_id[0]+graph.trace_id[1]+':')
            # print(score)
            trace_score_dict[graph.trace_id[0]+graph.trace_id[1]] = score
    return trace_score_dict

    
