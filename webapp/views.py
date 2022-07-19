from ModelPlatform.views import MPView, ResponseData
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_400_BAD_REQUEST

from webapp import services
from webapp.models import Span
from webapp.serializer import SpanSerializer

# Create your views here.


class DataProcessView(MPView):
    def get_complete_trace(self, request):
        '''
        Get complete traces
        '''
        response_data = ResponseData()
        try:
            filepath = self.check_and_get(
                request.data, 'filepath', response_data)
            services.get_data_file(self, request.data, filepath, response_data)
        except ValidationError as err:
            response_data.data = err.detail
            response_data.status = HTTP_400_BAD_REQUEST
        return self.response(response_data)
