from ModelPlatform.views import MPView, ResponseData
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_400_BAD_REQUEST

from webapp import services
from webapp.models import Span, Endpoint, MLAlgorithm, MLAlgorithmStatus, MLRequest
from webapp.serializer import SpanSerializer, EndpointSerializer, MLAlgorithmSerializer, MLAlgorithmStatusSerializer, MLRequestSerializer
from rest_framework import viewsets
from rest_framework import mixins

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
            after_merge_path = filepath + '-merge'
            services.change_trace(
                self, request.data, after_merge_path, response_data)
        except ValidationError as err:
            response_data.data = err.detail
            response_data.status = HTTP_400_BAD_REQUEST
        return self.response(response_data)


class EndpointViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = EndpointSerializer
    queryset = Endpoint.objects.all()


class MLAlgorithmViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = MLAlgorithmSerializer
    queryset = MLAlgorithm.objects.all()


def deactivate_other_statuses(instance):
    old_statuses = MLAlgorithmStatus.objects.filter(parent_mlalgorithm=instance.parent_mlalgorithm,
                                                    created_at__lt=instance.created_at,
                                                    active=True)
    for i in range(len(old_statuses)):
        old_statuses[i].active = False
    MLAlgorithmStatus.objects.bulk_update(old_statuses, ["active"])


class MLAlgorithmStatusViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet,
    mixins.CreateModelMixin
):
    serializer_class = MLAlgorithmStatusSerializer
    queryset = MLAlgorithmStatus.objects.all()

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save(active=True)
                # set active=False for other statuses
                deactivate_other_statuses(instance)

        except Exception as e:
            raise APIException(str(e))


class MLRequestViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet,
    mixins.UpdateModelMixin
):
    serializer_class = MLRequestSerializer
    queryset = MLRequest.objects.all()
