import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from django.db import transaction

from apps.tenants.models import Tenant
from apps.emissions.models import NormalizedEmission
from .models import IngestionBatch, RawRecord
from .serializers import IngestionBatchSerializer
from apps.emissions.serializers import NormalizedEmissionSerializer
from .parsers.sap import parse as parse_sap
from .parsers.utility import parse as parse_utility
from .parsers.travel import parse as parse_travel

logger = logging.getLogger(__name__)

PARSERS = {
    'sap': parse_sap,
    'utility': parse_utility,
    'travel': parse_travel,
}


def _get_tenant(request):
    tenant_id = request.query_params.get('tenant_id') or request.data.get('tenant_id')
    if not tenant_id:
        return None, Response(
            {'data': None, 'error': 'tenant_id is required', 'meta': {}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        return Tenant.objects.get(pk=tenant_id), None
    except Tenant.DoesNotExist:
        return None, Response(
            {'data': None, 'error': 'tenant not found', 'meta': {}},
            status=status.HTTP_404_NOT_FOUND,
        )


class UploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        source = request.data.get('source', '').lower()
        if source not in PARSERS:
            return Response(
                {'data': None, 'error': f"source must be one of: {list(PARSERS.keys())}", 'meta': {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenant, err = _get_tenant(request)
        if err:
            return err

        file = request.FILES.get('file')
        if not file:
            return Response(
                {'data': None, 'error': 'no file uploaded', 'meta': {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response(
                {'data': None, 'error': 'file must be UTF-8 encoded', 'meta': {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parse_fn = PARSERS[source]
        result = parse_fn(content)

        with transaction.atomic():
            batch = IngestionBatch.objects.create(
                tenant=tenant,
                source=source,
                uploaded_by=request.user,
                original_filename=file.name,
                total_rows=len(result['success']) + len(result['failed']),
                parsed_rows=len(result['success']),
                failed_rows=len(result['failed']),
            )

            for row in result['success']:
                raw = RawRecord.objects.create(
                    batch=batch,
                    row_number=row['row'],
                    raw_payload=row['raw'],
                )
                flag_reason = ''
                row_status = NormalizedEmission.STATUS_PENDING
                if row.get('warnings'):
                    row_status = NormalizedEmission.STATUS_FLAGGED
                    flag_reason = '; '.join(w['msg'] for w in row['warnings'])

                NormalizedEmission.objects.create(
                    tenant=tenant,
                    batch=batch,
                    raw_record=raw,
                    scope=row['scope'],
                    source=row['source'],
                    activity_date=row['activity_date'],
                    description=row.get('description', ''),
                    location=row.get('location', ''),
                    original_value=row['original_value'],
                    original_unit=row['original_unit'],
                    normalized_value=row['normalized_value'],
                    normalized_unit=row['normalized_unit'],
                    co2e_kg=row['co2e_kg'],
                    status=row_status,
                    flag_reason=flag_reason,
                )

            for row in result['failed']:
                RawRecord.objects.create(
                    batch=batch,
                    row_number=row['row'],
                    raw_payload=row['raw'],
                    parse_error=row['error'],
                )

        return Response({
            'data': IngestionBatchSerializer(batch).data,
            'error': None,
            'meta': {
                'parsed': len(result['success']),
                'failed': len(result['failed']),
                'warnings': len(result['warnings']),
            },
        }, status=status.HTTP_201_CREATED)


class BatchListView(APIView):
    def get(self, request):
        tenant, err = _get_tenant(request)
        if err:
            return err
        batches = IngestionBatch.objects.filter(tenant=tenant).order_by('-uploaded_at')
        return Response({
            'data': IngestionBatchSerializer(batches, many=True).data,
            'error': None,
            'meta': {'count': batches.count()},
        })


class BatchDetailView(APIView):
    def get(self, request, pk):
        tenant, err = _get_tenant(request)
        if err:
            return err
        try:
            batch = IngestionBatch.objects.get(pk=pk, tenant=tenant)
        except IngestionBatch.DoesNotExist:
            return Response({'data': None, 'error': 'batch not found', 'meta': {}}, status=status.HTTP_404_NOT_FOUND)

        emissions = NormalizedEmission.objects.filter(batch=batch).select_related('raw_record')
        return Response({
            'data': {
                'batch': IngestionBatchSerializer(batch).data,
                'emissions': NormalizedEmissionSerializer(emissions, many=True).data,
            },
            'error': None,
            'meta': {'count': emissions.count()},
        })
