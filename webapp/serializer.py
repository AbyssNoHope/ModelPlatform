from rest_framework import serializers

from .models import Span, OnlineDetection


class SpanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Span
        fields = '__all__'

class OnlineDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineDetection
        fields = '__all__'