from rest_framework.views import APIView
from rest_framework.response import Response


class ApproveView(APIView):
    def post(self, request, pk):
        return Response({'data': None, 'error': 'not implemented', 'meta': {}}, status=501)


class RejectView(APIView):
    def post(self, request, pk):
        return Response({'data': None, 'error': 'not implemented', 'meta': {}}, status=501)


class FlagView(APIView):
    def post(self, request, pk):
        return Response({'data': None, 'error': 'not implemented', 'meta': {}}, status=501)


class BulkApproveView(APIView):
    def post(self, request, pk):
        return Response({'data': None, 'error': 'not implemented', 'meta': {}}, status=501)
