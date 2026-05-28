import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from apps.emissions.models import NormalizedEmission
from apps.ingestion.models import IngestionBatch
from .models import AuditLog
from .serializers import AuditLogSerializer

logger = logging.getLogger(__name__)


def _get_emission(pk):
    try:
        return NormalizedEmission.objects.get(pk=pk), None
    except NormalizedEmission.DoesNotExist:
        return None, Response({'data': None, 'error': 'emission not found', 'meta': {}}, status=404)


def _log(emission, action, user, prev_status, new_status, note='', diff=None):
    AuditLog.objects.create(
        emission=emission,
        action=action,
        performed_by=user,
        previous_status=prev_status,
        new_status=new_status,
        note=note,
        diff=diff,
    )


class ApproveView(APIView):
    def post(self, request, pk):
        emission, err = _get_emission(pk)
        if err:
            return err
        if emission.status == NormalizedEmission.STATUS_APPROVED:
            return Response({'data': None, 'error': 'already approved', 'meta': {}}, status=400)

        prev = emission.status
        with transaction.atomic():
            emission.status = NormalizedEmission.STATUS_APPROVED
            emission.save(update_fields=['status', 'updated_at'])
            _log(emission, AuditLog.ACTION_APPROVE, request.user, prev, emission.status)

        return Response({'data': {'id': emission.id, 'status': emission.status}, 'error': None, 'meta': {}})


class RejectView(APIView):
    def post(self, request, pk):
        emission, err = _get_emission(pk)
        if err:
            return err
        if emission.status == NormalizedEmission.STATUS_APPROVED:
            return Response({'data': None, 'error': 'approved rows cannot be rejected', 'meta': {}}, status=400)

        prev = emission.status
        note = request.data.get('note', '')
        with transaction.atomic():
            emission.status = NormalizedEmission.STATUS_REJECTED
            emission.save(update_fields=['status', 'updated_at'])
            _log(emission, AuditLog.ACTION_REJECT, request.user, prev, emission.status, note=note)

        return Response({'data': {'id': emission.id, 'status': emission.status}, 'error': None, 'meta': {}})


class FlagView(APIView):
    def post(self, request, pk):
        emission, err = _get_emission(pk)
        if err:
            return err
        if emission.status == NormalizedEmission.STATUS_APPROVED:
            return Response({'data': None, 'error': 'approved rows cannot be flagged', 'meta': {}}, status=400)

        prev = emission.status
        reason = request.data.get('reason', '')
        with transaction.atomic():
            emission.status = NormalizedEmission.STATUS_FLAGGED
            emission.flag_reason = reason
            emission.save(update_fields=['status', 'flag_reason', 'updated_at'])
            _log(emission, AuditLog.ACTION_FLAG, request.user, prev, emission.status, note=reason)

        return Response({'data': {'id': emission.id, 'status': emission.status}, 'error': None, 'meta': {}})


class BulkApproveView(APIView):
    def post(self, request, pk):
        try:
            batch = IngestionBatch.objects.get(pk=pk)
        except IngestionBatch.DoesNotExist:
            return Response({'data': None, 'error': 'batch not found', 'meta': {}}, status=404)

        pending = NormalizedEmission.objects.filter(
            batch=batch,
            status__in=[NormalizedEmission.STATUS_PENDING],
        )

        approved_ids = []
        with transaction.atomic():
            for emission in pending:
                prev = emission.status
                emission.status = NormalizedEmission.STATUS_APPROVED
                emission.save(update_fields=['status', 'updated_at'])
                _log(emission, AuditLog.ACTION_APPROVE, request.user, prev, emission.status, note='bulk approve')
                approved_ids.append(emission.id)

        return Response({
            'data': {'approved_count': len(approved_ids), 'ids': approved_ids},
            'error': None,
            'meta': {},
        })


class AuditLogListView(APIView):
    def get(self, request, pk):
        try:
            emission = NormalizedEmission.objects.get(pk=pk)
        except NormalizedEmission.DoesNotExist:
            return Response({'data': None, 'error': 'emission not found', 'meta': {}}, status=404)

        logs = AuditLog.objects.filter(emission=emission).order_by('-performed_at')
        return Response({
            'data': AuditLogSerializer(logs, many=True).data,
            'error': None,
            'meta': {'count': logs.count()},
        })
