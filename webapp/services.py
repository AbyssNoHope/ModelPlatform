from rest_framework.exceptions import ValidationError

from webapp.views import MPView, ResponseData

from .models import Span
from .serializer import SpanSerializer
import os
import csv
import re
import time


def get_complete_trace(self: MPView, request_data, filepath, response_data: ResponseData):
    try:
        data_file = open(filepath, 'r')
        count = 0
        trace = []
        trace_id = ""
        for line in data_file:
            count += 1
            span = line.strip()
            if count % 10000 == 0:
                print('sum: %d' % count)
            if span.split(';')[1] != trace_id:
                if len(trace) > 1:
                    merge(trace, filepath)
                trace = []
                trace.append(span)
                trace_id = span.split(';')[1]
            else:
                trace.append(span)
    except FileNotFoundError:
        raise ValidationError('未找到该文件: %s' % filepath)


def merge(single_trace, filepath):
    after_merge_path = filepath + '-merge'
    if os.path.exists(after_merge_path):
        os.remove(after_merge_path)
    file = open(after_merge_path, 'a')
    spanid_pspanid, spid_span = get_span_pspan_dict(single_trace)
    judge = 1
    while judge != 0:
        judge = 0
        for span in single_trace:
            single = span.strip().split(';')
            span_id = single[2]
            if span_id in spid_span.keys() and spanid_pspanid[span_id] != '':
                sp_span = spid_span[span_id].split(';')
                ps_span = spid_span[spanid_pspanid[span_id]].split(';')
                if sp_span[-1] == ps_span[-1]:
                    judge += 1
                    spanid_list = []
                    for spanid in spanid_pspanid.keys():
                        if sp_span[2] == spanid_pspanid[spanid]:
                            spanid_list.append(spanid)
                    if len(spanid_list) != 0:
                        for i in spanid_list:
                            spanid_pspanid[i] = ps_span[2]
                            new_span = spid_span[i].strip().split(';')
                            spid_span[i] = new_span[0] + ';' + new_span[1] + ';' + new_span[2] + ';' + new_span[3] + ';' + ps_span[2] + \
                                ';' + new_span[5] + ';' + new_span[6] + ';' + \
                                new_span[7] + ';' + \
                                new_span[8] + ';' + new_span[9]
                    spid_span.pop(span_id)
                    spanid_pspanid.pop(span_id)
    for i in spid_span.values():
        file.write(i+'\n')
    file.close()


def get_span_pspan_dict(single_trace):
    sp_psp = dict()
    spid_span = dict()
    for span in single_trace:
        single = span.strip().split(';')
        sp_psp[single[2]] = single[4]
        spid_span[single[2]] = span
    return sp_psp, spid_span


def change_trace(self: MPView, request_data, filepath, response_data: ResponseData):
    try:
        os.mkdir('data/service2/')
        try:
            file = open(filepath, 'r')
            for line in file:
                span_information = line.strip().split(';')
                span_serializer = SpanSerializer(data={
                    'trace_id_high': span_information[1][0:16],
                    'trace_id_low': span_information[1][16:32],
                    'span_id': span_information[2],
                    'parent_span_id': span_information[4],
                    'service_name': span_information[9],
                    'operation_name': span_information[8],
                    'st_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(span_information[6])/1000000)),
                    'duration': span_information[7],
                    'nanosecond': span_information[6]
                })
                if not span_serializer.is_valid():
                    raise ValidationError(
                        '新建span记录失败' + str(span_serializer.errors))
                span = span_serializer.save()
                response_data.data = SpanSerializer(span).data
        except FileNotFoundError:
            raise ValidationError('未找到该文件: %s' % filepath)
    except FileExistsError:
        raise ValidationError('service2文件夹已存在, 请删除后重试!')
