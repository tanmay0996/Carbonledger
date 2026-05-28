from django.db import models
from django.contrib.auth.models import User
from apps.emissions.models import NormalizedEmission


class AuditLog(models.Model):
    ACTION_APPROVE = 'approve'
    ACTION_REJECT = 'reject'
    ACTION_FLAG = 'flag'
    ACTION_EDIT = 'edit'
    ACTION_CHOICES = [
        (ACTION_APPROVE, 'Approved'),
        (ACTION_REJECT, 'Rejected'),
        (ACTION_FLAG, 'Flagged'),
        (ACTION_EDIT, 'Edited'),
    ]

    emission = models.ForeignKey(NormalizedEmission, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    note = models.TextField(blank=True, default='')
    diff = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.action} on emission {self.emission_id} by {self.performed_by}"
