from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from apps.tenants.models import Tenant
from apps.ingestion.models import IngestionBatch, RawRecord


class NormalizedEmission(models.Model):
    SCOPE_1 = 1
    SCOPE_2 = 2
    SCOPE_3 = 3
    SCOPE_CHOICES = [(1, 'Scope 1'), (2, 'Scope 2'), (3, 'Scope 3')]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_FLAGGED = 'flagged'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_FLAGGED, 'Flagged'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='emissions')
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name='emissions')
    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE, related_name='emission', null=True, blank=True)

    scope = models.IntegerField(choices=SCOPE_CHOICES)
    source = models.CharField(max_length=20)
    activity_date = models.DateField()
    description = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=255, blank=True)

    original_value = models.DecimalField(max_digits=18, decimal_places=4)
    original_unit = models.CharField(max_length=50)
    normalized_value = models.DecimalField(max_digits=18, decimal_places=4)
    normalized_unit = models.CharField(max_length=50)
    co2e_kg = models.DecimalField(max_digits=18, decimal_places=4)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    flag_reason = models.TextField(blank=True, default='')
    manually_edited = models.BooleanField(default=False)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_emissions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                current = NormalizedEmission.objects.get(pk=self.pk)
            except NormalizedEmission.DoesNotExist:
                current = None
            if current and current.status == self.STATUS_APPROVED:
                update_fields = kwargs.get('update_fields')
                # Only allow the status field itself to change (for the approve idempotency check)
                # Any other field change on an approved row is blocked
                if update_fields and set(update_fields) - {'status', 'updated_at'}:
                    raise ValidationError('Approved rows are locked and cannot be edited.')
                if not update_fields:
                    raise ValidationError('Approved rows are locked and cannot be edited.')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Scope {self.scope} | {self.co2e_kg} kgCO2e | {self.status}"
