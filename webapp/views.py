from ModelPlatform.views import MPView, ResponseData
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_400_BAD_REQUEST

from webapp import services
from webapp.models import Span
from webapp.serializer import SpanSerializer

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
