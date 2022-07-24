# coding=utf-8
import argparse
import sys
import time
import requests
import json
import click
import yaml
import datetime
from online_detection.evaluate import *

from elasticsearch import Elasticsearch

''' 
client 在线检测客户端
1. 每分钟查询两次ES:
    a.获取过去6min-5min之间的结算traceIDs；
    b.根据traceIDs获取trace列表；
2. 请求tensorflow serving 接口，获取检测输入STV向量维度。
3. 将trace列表中每条处理为对应维度STV向量。
4. 将所有处理后的STV向量处理成一个batch（二维数组，每一行为一个STV向量）。
5. 请求tensorflow serving服务端trace异常检测接口，返回异常分数列表（每一维代表对应trace(STV向量)异常分数值）。
6. 根据异常分数判断是否为异常
'''


class Client:
    eshost = ""
    account = ""
    password = ""
    tensorflowserving = ""
    jaegerUrl = ""
    wechatrobot = ""
    indexing = ""
    score = 0
    templ = '{"msgtype": "markdown","markdown": {"content": "AIOps<font color="warning">trace-anamoly ' \
            '告警</font>，请相关同事注意。\n>traceID:<font color="comment">{0}</font>>jaeger链接:<font color="comment">{1}</font>"}}'
    __es = Elasticsearch()

    def __init__(self, args):
        self.tensorflowserving = args["tensorflowserving"]
        self.jaegerUrl = args["jaegerUrl"]
        self.wechatrobot = args["wechatrobot"]
        self.score = args["score"]
        self.__es = Elasticsearch(hosts=args["eshost"], http_auth=(args["account"], args["password"]))

        now = time.strftime("%Y.%m.%d", time.localtime())
        self.indextrans = "{}{}".format(args["indextrans"], now)
        self.indexspan = "{}{}".format(args["indexspan"], now)

    # 从ES获取过去6min-过去5min traceIDs
    def getDetectTraceIDsFromES(self):
        startTime = self.timeStampFewMinuteAgo(6)
        endTime = self.timeStampFewMinuteAgo(5)

        query_json = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "timestamp.us": {
                                    "gte": startTime,  # >=开始时间戳
                                    "lt": endTime  # < 结束时间戳
                                }
                            }
                        }
                    ],
                    "must_not": [
                        {
                            "terms": {
                                "service.name": [
                                    "apm-server", "opsflow", "noah", "notice_consume", "flowable", "alarm_notice"
                                ]
                            }
                        },
                        {
                            "exists": {
                                "field": "parent.id"
                            }
                        }
                    ]
                }
            }
        }

        # scroll='5m' 游标查询的过期时间，保持游标查询窗口需要消耗资源，如果不再需要维护这种资源就该早点释放掉，这个时间需要足够处理当前批的结果
        query = self.__es.search(index=self.indextrans, body=query_json)
        print (query)
        results = query['hits']['hits']  # es查询出的结果第一页
        traceIDs = []
        serviceNameList = []
        for item in results:
            traceData = item["_source"]
            traceIDs.append(traceData["trace"]["id"])
            serviceNameList.append(traceData["service"]["name"])
        return traceIDs, serviceNameList

    # timeStampFewMinuteAgo 获取距当前时间 ago分钟前的毫秒时间戳
    def timeStampFewMinuteAgo(self, ago):
        return int((time.time() - int(ago) * 60) * 1000000)

    # processOperationName 处理operationName /XXX/123(订单号) -> /XXX
    def __processOperationName(self, operationName):
        routeList = operationName.split("/")
        if len(routeList) <= 1:
            return operationName
        lastItem = routeList[len(routeList) - 1]
        if lastItem.isnumeric():
            s = "/"
            return s.join(routeList[:len(routeList) - 1])
        return operationName

    # getRawTraceListByTraceIDs 获取原始trace
    def __queryTransaction(self, traceID):
        query_json = {
            "query": {
                "match": {
                    "trace.id": traceID
                }
            }
        }

        # scroll='5m' 游标查询的过期时间，保持游标查询窗口需要消耗资源，如果不再需要维护这种资源就该早点释放掉，这个时间需要足够处理当前批的结果
        query = self.__es.search(index=self.indextrans, body=query_json)
        results = query['hits']['hits']  # es查询出的结果第一页

        transid2line = dict()
        for item in results:
            transactionData = item["_source"]

            parentTraceID = ""
            parentSpanID = ""
            refType = ""
            traceStartTime = ""
            operationName = self.__processOperationName(transactionData["transaction"]["name"])
            try:
                parentid = transactionData["parent"]["id"]
            except KeyError:
                parentid = ""
            if parentid != "":
                parentTraceID = transactionData["trace"]["id"]
                parentSpanID = transactionData["parent"]["id"]
            else:
                traceStartTime = str(transactionData["timestamp"]["us"])
            if traceStartTime == '0':
                traceStartTime = ""
            transid2line[transactionData["transaction"]["id"]] = "{};{};{};{};{};{};{};{};{};{}". \
                format(traceStartTime, transactionData["trace"]["id"], transactionData["transaction"]["id"],
                       parentTraceID,
                       parentSpanID, refType, transactionData["timestamp"]["us"],
                       transactionData["transaction"]["duration"]["us"], operationName,
                       transactionData["service"]["name"])

        return transid2line

    # getRawTraceListByTraceIDs 获取原始trace
    def __querySpan(self, transactionID):
        query_json = {
            "query": {
                "match": {
                    "parent.id": transactionID
                }
            },
            "sort": [
                {
                    "timestamp.us": {
                        "order": "asc"  # asc\desc  升序\降序
                    }
                }
            ]
        }

        # scroll='5m' 游标查询的过期时间，保持游标查询窗口需要消耗资源，如果不再需要维护这种资源就该早点释放掉，这个时间需要足够处理当前批的结果
        query = self.__es.search(index=self.indexspan, body=query_json)
        results = query['hits']['hits']

        spanList = []
        olderSpanID = ""
        for j, item in enumerate(results):
            traceStartTime = ""
            refType = ""

            span = item["_source"]
            if j == 0:
                line = "{};{};{};{};{};{};{};{};{};{}".format(traceStartTime, span["trace"]["id"], span["span"]["id"],
                                                              span["trace"]["id"], transactionID, refType,
                                                              span["timestamp"]["us"], span["span"]["duration"]["us"],
                                                              span["span"]["name"], span["service"]["name"])
                olderSpanID = span["span"]["id"]
                spanList.append(line)
                continue

            line = "{};{};{};{};{};{};{};{};{};{}".format(traceStartTime, span["trace"]["id"], span["span"]["id"],
                                                          span["trace"]["id"], olderSpanID, refType,
                                                          span["timestamp"]["us"], span["span"]["duration"]["us"],
                                                          span["span"]["name"], span["service"]["name"])
            olderSpanID = span["span"]["id"]
            spanList.append(line)
        return spanList

    def getRawTraceListByTraceIDs(self, traceIDList):
        rawTraceList = []
        for traceId in traceIDList:
            transId2line = self.__queryTransaction(traceId)
            if len(transId2line) == 0:
                continue
            for _, v in transId2line.items():
                rawTraceList.append(v)
            for k, v in transId2line.items():
                spanList = self.__querySpan(k)
                if len(spanList) == 0:
                    continue
                for line in spanList:
                    rawTraceList.append(line)
        return rawTraceList

    # getAnomalyScore 查询tensorflow serving STV向量batch对应异常分数
    def getAnomalyScore(self, instances):
        # TODO RC-172.16.6.25 PROD-172.16.81.143
        data = json.dumps({"instances": instances})  # instances 二维数组,STV向量batch
        headers = {"content-type": "application/json"}
        json_response = requests.post('http://{}:8501/v1/models/traceAnomaly:predict'.format(self.tensorflowserving),
                                      data=data,
                                      headers=headers)

        try:
            predictions = json.loads(json_response.text)
            res = predictions["predictions"]
        except KeyError:
            return ""
        return res

    # getModelDimension 请求tensorflow serving 获取traceAnomaly模型输入维度（TODO 日后优化，模型训练、检测固定输入维度）
    def getModelDimension(self):
        # TODO RC-172.16.6.25 PROD-172.16.81.143
        json_response = requests.get('http://{}:8501/v1/models/traceAnomaly/metadata'.format(self.tensorflowserving))
        predictions = json.loads(json_response.text)
        dimension = \
            predictions["metadata"]["signature_def"]["signature_def"]["serving_default"]["inputs"]["input"][
                "tensor_shape"][
                "dim"][1]["size"]
        print("model dimension=", dimension)

        return int(dimension)

    def detectAnomalyByScore(self, score):
        if score < self.score:
            return True
        return False

    def sendWeChatRobot(self, serviceName, traceID):
        # TODO
        esapmUrl = "https://user-kibana.yunzhanghu.net/s/yzh/app/apm/services/{}/overview?kuery=trace.id:{}&rangeFrom=now-15h&rangeTo=now&latencyAggregationType=avg&transactionType=request&comparisonEnabled=true&comparisonType=week".format(
            serviceName, traceID)
        content = """
        AIOps <font color=\"warning\">trace-anamoly 告警</font>，请相关同事注意。
             >traceID:<font color=\"comment\">{0}</font>
             >起始serviceName: <font color=\"comment\">{1}</font>
             >[esapm链接]({2})
             """
        content = content.format(traceID, serviceName, esapmUrl)

        templ = {
            'msgtype': 'markdown',
            'markdown': {
                'content': content
            }
        }
        data = json.dumps(templ)  # instances 二维数组,STV向量batch
        headers = {"content-type": "application/json"}
        # TODO
        json_response = requests.post(self.wechatrobot, data=data, headers=headers)
        _ = json.loads(json_response.text)
        return


def load_env(env_file_name):
    f = open("./client/config/{}".format(env_file_name), 'r')
    cfg = yaml.safe_load(f)
    return cfg

def detection(model_name):
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-env', type=str, help="current env")
    parser.add_argument('-dimension', type=int, help="dimension")

    args = parser.parse_args()

    conf = {}
    if args.env == 'rc':
        conf = load_env('dev.yml')
    elif args.env == 'prod':
        conf = load_env('prod.yml')

    # 获取traceIDs
    client = Client(conf)

    traceIDs, serviceNameList = client.getDetectTraceIDsFromES()
    if len(traceIDs) == 0:
        sys.exit(0)
    traceIDServiceName = dict(zip(traceIDs, serviceNameList))
    print("123455")

    # 根据traceIDs获取原始trace数据
    rawTraces = client.getRawTraceListByTraceIDs(traceIDs)
    if len(rawTraces) == 0:
        sys.exit(0)
    
    save_data_path = '../online_data/'+str(datetime.date.today())
    f =  open(save_data_path, 'w')
    for span in rawTraces:
        f.write(span+'\n')
    
    f.close()
    
    #{traceid: score}
    trace_score_dict = evaluate_nll(save_data_path, model_name)
    return trace_score_dict

    # 转换为STV向量
    # stv_batch_tmp = STV_list(rawTraces, args.dimension)
    # stv_batch, flow = model_input(stv_batch_tmp, "./client/config/valid_column")
    # print(stv_batch[0])
    # traceIDList = []
    # batchSTV = []
    # traceIDBatch = []
    # i = 0

    # for stv in stv_batch_tmp:
    #     traceIDWithSTV = stv.split(':')
    #     traceIDList.append(traceIDWithSTV[0])
    # traceID2STV = dict(zip(traceIDList, stv_batch[0]))
    # print(traceID2STV)

    # for traceID, stv in traceID2STV.items():
    #     stv = map(float, stv)
    #     batchSTV.append(list(stv))
    #     traceIDBatch.append(traceID)
    #     i += 1

    #     if i == 100:
    #         # 请求tensorflow serving
    #         scoreList = client.getAnomalyScore(batchSTV)
    #         if len(scoreList) == 0:
    #             continue
    #         traceID2Score = dict(zip(traceIDBatch, scoreList))
    #         print(traceID2Score)
    #         # 根据异常分数判断是否为异常
    #         for traceID, score in traceID2Score.items():
    #             if client.detectAnomalyByScore(float(score)):
    #                 # 推送机器人
    #                 client.sendWeChatRobot(traceIDServiceName[traceID], traceID)
    #         i = 0
    #         traceIDBatch = []
    #         batchSTV = []

    # if i < 100:
    #     scoreList = client.getAnomalyScore(batchSTV)
    #     traceID2Score = dict(zip(traceIDBatch, scoreList))
    #     print(traceID2Score)
    #     # 根据异常分数判断是否为异常
    #     for traceID, score in traceID2Score.items():
    #         if client.detectAnomalyByScore(float(score)):
    #             # 推送机器人
    #             client.sendWeChatRobot(traceIDServiceName[traceID], traceID)


