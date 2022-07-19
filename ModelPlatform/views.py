
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK


class ResponseData:
    def __init__(self, data='请求成功', status=HTTP_200_OK):
        self.data = data
        self.status = status


class MPView(APIView):

    @staticmethod
    def check_and_get(data, field, response_data):
        value = data.get(field)
        if value is None:
            raise ValidationError('请求缺少字段%s' % field)
        else:
            return value

    @staticmethod
    def response(response_data):
        return Response(data={'data': response_data.data}, status=response_data.status)
