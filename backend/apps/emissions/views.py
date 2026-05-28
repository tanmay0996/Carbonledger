from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum

from apps.tenants.models import Tenant
from .models import NormalizedEmission
from .serializers import NormalizedEmissionSerializer


def _get_tenant(request):
    tenant_id = request.query_params.get('tenant_id')
    if not tenant_id:
        return None, Response({'data': None, 'error': 'tenant_id is required', 'meta': {}}, status=400)
    try:
        return Tenant.objects.get(pk=tenant_id), None
    except Tenant.DoesNotExist:
        return None, Response({'data': None, 'error': 'tenant not found', 'meta': {}}, status=404)


class EmissionListView(APIView):
    def get(self, request):
        tenant, err = _get_tenant(request)
        if err:
            return err

        qs = NormalizedEmission.objects.filter(tenant=tenant).order_by('-activity_date')

        batch_id = request.query_params.get('batch_id')
        if batch_id:
            qs = qs.filter(batch_id=batch_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        scope = request.query_params.get('scope')
        if scope:
            qs = qs.filter(scope=scope)

        return Response({
            'data': NormalizedEmissionSerializer(qs, many=True).data,
            'error': None,
            'meta': {'count': qs.count()},
        })


class SummaryView(APIView):
    def get(self, request):
        tenant, err = _get_tenant(request)
        if err:
            return err

        approved = NormalizedEmission.objects.filter(
            tenant=tenant,
            status=NormalizedEmission.STATUS_APPROVED,
        )

        summary = {}
        for scope in [1, 2, 3]:
            total = approved.filter(scope=scope).aggregate(total=Sum('co2e_kg'))['total'] or 0
            summary[f'scope_{scope}'] = float(total)

        summary['total'] = sum(summary.values())

        return Response({'data': summary, 'error': None, 'meta': {}})
