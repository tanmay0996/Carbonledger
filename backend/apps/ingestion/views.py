from rest_framework.views import APIView
from rest_framework.response import Response


class UploadView(APIView):
    def post(self, request):
        return Response({'data': None, 'error': 'not implemented', 'meta': {}}, status=501)


class BatchListView(APIView):
    def get(self, request):
        return Response({'data': [], 'error': None, 'meta': {}})


class BatchDetailView(APIView):
    def get(self, request, pk):
        return Response({'data': None, 'error': 'not implemented', 'meta': {}}, status=501)
