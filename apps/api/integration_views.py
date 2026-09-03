from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import PaymentWebhookSerializer
from apps.integrations.services import process_payment_webhook
from apps.integrations.models import ExternalEvent


class PaymentWebhookView(APIView):
    def post(self, request):
        serializer = PaymentWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = process_payment_webhook(
            external_event_id=serializer.validated_data["external_event_id"],
            event_type=serializer.validated_data["event_type"],
            order_id=serializer.validated_data["order_id"],
            payment_amount=serializer.validated_data["payment_amount"],
        )

        if event.processing_status == ExternalEvent.ProcessingStatus.FAILED:
            return Response(
                {
                    "error": "PAYMENT_WEBHOOK_FAILED",
                    "external_event_id": event.external_event_id,
                    "detail": event.error_message,
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "external_event_id": event.external_event_id,
                "processing_status": event.processing_status,
            },
            status=status.HTTP_200_OK,
        )
