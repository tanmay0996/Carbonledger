from rest_framework import serializers
from .models import IngestionBatch, RawRecord


class IngestionBatchSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField()

    class Meta:
        model = IngestionBatch
        fields = [
            'id', 'tenant', 'source', 'uploaded_by', 'uploaded_at',
            'total_rows', 'parsed_rows', 'failed_rows', 'original_filename',
        ]


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ['id', 'batch', 'row_number', 'raw_payload', 'parse_error', 'created_at']
