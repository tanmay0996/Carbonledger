from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    performed_by = serializers.StringRelatedField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'emission', 'action', 'performed_by', 'performed_at',
            'previous_status', 'new_status', 'note', 'diff',
        ]
