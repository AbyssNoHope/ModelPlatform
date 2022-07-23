from rest_framework import serializers

from .models import Span


class SpanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Span
        fields = '__all__'
