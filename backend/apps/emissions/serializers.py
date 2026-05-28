from rest_framework import serializers
from .models import NormalizedEmission


class NormalizedEmissionSerializer(serializers.ModelSerializer):
    edited_by = serializers.StringRelatedField()

    class Meta:
        model = NormalizedEmission
        fields = [
            'id', 'tenant', 'batch', 'raw_record', 'scope', 'source',
            'activity_date', 'description', 'location',
            'original_value', 'original_unit',
            'normalized_value', 'normalized_unit', 'co2e_kg',
            'status', 'flag_reason', 'manually_edited', 'edited_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['tenant', 'batch', 'raw_record', 'scope', 'source', 'created_at', 'updated_at']
