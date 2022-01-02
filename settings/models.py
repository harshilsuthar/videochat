from django.db import models
from django.utils import timezone


class CreateTimeStamp(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(editable=False)

class UpdateTimeStamp(models.Model):
    class Meta:
        abstract = True

    updated_at = models.DateTimeField()
