from django.db import models
from django.contrib.auth.models import User
from apps.tenants.models import Tenant


class IngestionBatch(models.Model):
    SOURCE_SAP = 'sap'
    SOURCE_UTILITY = 'utility'
    SOURCE_TRAVEL = 'travel'
    SOURCE_CHOICES = [
        (SOURCE_SAP, 'SAP'),
        (SOURCE_UTILITY, 'Utility'),
        (SOURCE_TRAVEL, 'Travel'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='batches')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_rows = models.IntegerField(default=0)
    parsed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    original_filename = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.source} batch {self.pk} — {self.uploaded_at:%Y-%m-%d}"


class RawRecord(models.Model):
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name='raw_records')
    row_number = models.IntegerField()
    raw_payload = models.JSONField()
    parse_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Row {self.row_number} of batch {self.batch_id}"
