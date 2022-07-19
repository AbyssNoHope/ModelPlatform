from rest_framework.exceptions import ValidationError

from webapp.views import MPView, ResponseData

from .models import Span
from .serializer import SpanSerializer


def get_data_file(self: MPView, request_data, filepath, response_data: ResponseData):
    try:
        data_file = open(filepath, 'r')
        # read data
    except FileNotFoundError as err:
        raise ValidationError('未找到该文件: %s' % filepath)
