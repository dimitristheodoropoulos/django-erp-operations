from rest_framework.response import Response
from rest_framework.views import APIView


class ApiRootView(APIView):
    """
    Minimal API v1 foundation endpoint.

    This endpoint verifies that the API application boundary,
    routing, and DRF integration are operational.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "name": "Django ERP Operations Platform API",
                "version": "1.0",
                "status": "ok",
            }
        )
