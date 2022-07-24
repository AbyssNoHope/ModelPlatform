# 获取spid: parent span字典
# 获取spid: span字典
def get_span_pspan_dict(single_trace):
    sp_psp = dict()
    spid_span = dict()
    for span in single_trace:
        single = span.strip().split(';')
        sp_psp[single[2]] = single[4]
        spid_span[single[2]] = span
    return sp_psp, spid_span

def merge(traces, filepath):
    after_merge_path = filepath + '-merge'
    f = open(after_merge_path, 'w')
    for single_trace in traces:
        spanid_pspanid, spid_span = get_span_pspan_dict(single_trace)
        #judge用来判断是否还需要继续合并
        judge = 1
        #已经处理过的span id
        while judge!=0:
            judge = 0
            for span in single_trace:
                single = span.strip().split(';')
                span_id = single[2]
                if span_id in spid_span.keys() and spanid_pspanid[span_id]!='':
                    #当前spanid对应的span
                    sp_span = spid_span[span_id].split(';')
                    # print(span_id)
                    # print(spanid_pspanid[span_id])
                    #父spanid对应的span
                    ps_span = spid_span[spanid_pspanid[span_id]].split(';')
                    if sp_span[-1] == ps_span[-1]:
                        judge += 1
                        #找到当前spanid的子spanid
                        spanid_list = []
                        for spanid in spanid_pspanid.keys():
                            if sp_span[2] == spanid_pspanid[spanid]:
                                spanid_list.append(spanid)
                        if len(spanid_list)!=0:
                            for i in spanid_list:
                                spanid_pspanid[i] = ps_span[2]
                                new_span = spid_span[i].strip().split(';')
                                spid_span[i] = new_span[0] + ';' + new_span[1] + ';' + new_span[2] + ';' + new_span[3] + ';' + ps_span[2] + \
                                    ';' + new_span[5] + ';' + new_span[6] + ';' + new_span[7] + ';' + new_span[8]+ ';' + new_span[9] 
                    
                        #删除被合并的spanid
                        spid_span.pop(span_id)
                        spanid_pspanid.pop(span_id)
        for i in spid_span.values():
            f.write(i+'\n')
    f.close()
     
# 获得完整的trace
def get_complete_trace(filepath):
    count = 0
    with open(filepath, 'r') as fp:
        traces = []
        trace = []
        traceid = ""
        for span in fp:
            count += 1
            sp = span.strip()
            si = sp.split(';')
            if count%10000 == 0:
                print('sum:%d'%(count))
            # 表明trace是空的
            if si[1] != traceid:
                if len(trace)>1:
                    traces.append(trace)
                trace = []
                trace.append(sp)
                traceid = si[1]
            else:
                trace.append(sp)  
    merge(traces, filepath)
