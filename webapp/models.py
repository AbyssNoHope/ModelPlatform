from __future__ import unicode_literals
from django.db import models

# Create your models here.


class Span(models.Model):
    trace_id_high = models.CharField(max_length=16)
    trace_id_low = models.CharField(max_length=16)
    span_id = models.CharField(max_length=16)
    parent_span_id = models.CharField(max_length=16)
    service_name = models.CharField(max_length=50)
    operation_name = models.CharField(max_length=100)
    st_time = models.CharField(max_length=20)
    duration = models.IntegerField()
    nanosecond = models.CharField(max_length=20)

    def __unicode__(self):
        return self.span_id

class OnlineDetection(models.Model):
    threshold = models.CharField(max_length=16)
    
    
