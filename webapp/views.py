from urllib import response
from ModelPlatform.views import MPView, ResponseData
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework import views, status
from rest_framework.response import Response

from webapp import services
from webapp.models import Span, OnlineDetection
from webapp.serializer import SpanSerializer,OnlineDetectionSerializer
from online_detection.get_threshold import *
from online_detection.online_detection_main import *
from rest_framework.utils import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# Create your views here.


class DataProcessView(MPView):
    def gen_csv(self, request):
        '''
        generate modified data file
        '''
        response_data = ResponseData()
        try:
            filepath = self.check_and_get(
                request.data, 'filepath', response_data)
            services.get_complete_trace(
                self, request.data, filepath, response_data)
            filename = filepath.split('/')[-1]
            after_merge_filename = filename + '-merge'
            after_merge_path = filepath + '-merge'
            services.change_trace(
                self, request.data, after_merge_path, response_data)
        except ValidationError as err:
            response_data.data = err.detail
            response_data.status = HTTP_400_BAD_REQUEST
        return self.response(response_data)

'''
    get threshold and online detection
'''
def save_threshold():
    threshold = get_threshold()
    ser = OnlineDetectionSerializer(data={"threshold": threshold})
    if not ser.is_valid():
        raise ValidationError('未获取到阈值')
    ser.save()

class OnlineDetectionView(views.APIView):
    # get threshold
    threshold_ob = OnlineDetection.objects().all()
    ser = OnlineDetectionSerializer(instance=threshold_ob)
    threshold = float(ser.values()[0])
    
    @require_http_methods(['GET'])
    def onlinedetection(request):
        trace_score_dict = detection()
        response = {}
        try:
            response['list'] = trace_score_dict
            response['msg'] = "success"
            response['error_num'] = 0
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1
        
        return JsonResponse(response)
            
        
    
