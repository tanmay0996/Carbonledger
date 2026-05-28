from rest_framework.views import APIView
from rest_framework.response import Response


class EmissionListView(APIView):
    def get(self, request):
        return Response({'data': [], 'error': None, 'meta': {}})


class SummaryView(APIView):
    def get(self, request):
        return Response({'data': {}, 'error': None, 'meta': {}})
