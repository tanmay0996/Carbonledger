from django.contrib import admin
from .models import IngestionBatch, RawRecord

admin.site.register(IngestionBatch)
admin.site.register(RawRecord)
