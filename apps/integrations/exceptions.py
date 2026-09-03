class PaymentWebhookFailed(Exception):
    """Raised when a payment webhook cannot be processed successfully."""

    def __init__(self, external_event_id, message):
        self.external_event_id = external_event_id
        self.message = message
        super().__init__(message)
