import logging

import pytest
from django.conf import settings

from apps.orders.exceptions import (
    InactiveCustomer,
    InvalidOrderQuantity,
    InvalidOrderState,
    OrderConfirmationError,
    OrderHasNoLines,
    OrderNotFound,
)
from apps.orders.services import cancel_order


class TestBusinessErrorContract:
    def test_business_exceptions_have_common_application_error_contract(self):
        exceptions = (
            OrderNotFound,
            InvalidOrderState,
            InactiveCustomer,
            OrderHasNoLines,
            InvalidOrderQuantity,
        )

        for exception_class in exceptions:
            assert issubclass(
                exception_class,
                OrderConfirmationError,
            )

    @pytest.mark.django_db
    def test_business_error_response_uses_consistent_envelope(
        self,
        operations_api_client,
    ):
        response = operations_api_client.post(
            "/api/v1/orders/00000000-0000-0000-0000-000000000000/cancel/",
            {},
            format="json",
        )

        assert response.status_code == 404
        assert "error" in response.data
        assert isinstance(response.data["error"], dict)
        assert "code" in response.data["error"]
        assert "message" in response.data["error"]


class TestConsistentAPIErrorContract:
    @pytest.mark.django_db
    def test_validation_error_uses_error_envelope(
        self,
        operations_api_client,
    ):
        response = operations_api_client.post(
            "/api/v1/orders/",
            {},
            format="json",
        )

        assert response.status_code == 400
        assert "error" in response.data
        assert isinstance(response.data["error"], dict)
        assert response.data["error"]["code"] == "VALIDATION_ERROR"
        assert "message" in response.data["error"]

    @pytest.mark.django_db
    def test_business_error_uses_same_top_level_envelope(
        self,
        operations_api_client,
    ):
        response = operations_api_client.post(
            "/api/v1/orders/00000000-0000-0000-0000-000000000000/cancel/",
            {},
            format="json",
        )

        assert "error" in response.data
        assert isinstance(response.data["error"], dict)
        assert "code" in response.data["error"]
        assert "message" in response.data["error"]

    @pytest.mark.django_db
    def test_payment_webhook_error_uses_same_error_envelope(
        self,
        operations_api_client,
    ):
        response = operations_api_client.post(
            "/api/v1/webhooks/payment/",
            {},
            format="json",
        )

        assert "error" in response.data
        assert isinstance(response.data["error"], dict)
        assert "code" in response.data["error"]
        assert "message" in response.data["error"]


class TestUnexpectedErrorHandling:
    def test_rest_framework_has_central_exception_handler(self):
        rest_framework_settings = getattr(settings, "REST_FRAMEWORK", {})

        assert rest_framework_settings.get("EXCEPTION_HANDLER"), (
            "ERP-REQ-043 requires a centralized DRF exception handler"
        )

    @pytest.mark.django_db
    def test_unexpected_error_contract_is_safe(
        self,
        operations_api_client,
        monkeypatch,
    ):
        import apps.api.order_views as order_views

        def raise_unexpected_error(*args, **kwargs):
            raise RuntimeError("SECRET_INTERNAL_FAILURE")

        monkeypatch.setattr(
            order_views,
            "cancel_order",
            raise_unexpected_error,
        )

        operations_api_client.raise_request_exception = False

        response = operations_api_client.post(
            "/api/v1/orders/00000000-0000-0000-0000-000000000000/cancel/",
            {},
            format="json",
        )

        assert response.status_code == 500
        assert response.data["error"]["code"] == "INTERNAL_ERROR"
        assert response.data["error"]["message"] != "SECRET_INTERNAL_FAILURE"
        assert "SECRET_INTERNAL_FAILURE" not in str(response.data)


class TestApplicationLogging:
    @pytest.mark.django_db
    def test_order_state_transition_emits_application_log(
        self,
        order,
        caplog,
    ):
        with caplog.at_level(logging.INFO):
            cancel_order(order.id)

        assert any(
            record.__dict__.get("event") == "order_state_transition"
            for record in caplog.records
        )

    def test_application_has_logging_configuration(self):
        assert getattr(settings, "LOGGING", None), (
            "ERP-REQ-044 requires application logging configuration"
        )

    @pytest.mark.django_db
    def test_unexpected_errors_are_logged(
        self,
        operations_api_client,
        monkeypatch,
        caplog,
    ):
        import apps.api.order_views as order_views

        def raise_unexpected_error(*args, **kwargs):
            raise RuntimeError("unexpected-test-failure")

        monkeypatch.setattr(
            order_views,
            "cancel_order",
            raise_unexpected_error,
        )

        operations_api_client.raise_request_exception = False

        with caplog.at_level(logging.ERROR):
            response = operations_api_client.post(
                "/api/v1/orders/00000000-0000-0000-0000-000000000000/cancel/",
                {},
                format="json",
            )

        assert response.status_code == 500

        unexpected_records = [
            record
            for record in caplog.records
            if record.name == "apps.api.exceptions"
            and record.levelno >= logging.ERROR
        ]

        assert unexpected_records

        record = unexpected_records[0]

        assert record.__dict__.get("event") == "unexpected_application_error"
        assert record.__dict__.get("exception_type") == "RuntimeError"
        assert record.__dict__.get("view") == "OrderCancelView"
        assert record.__dict__.get("method") == "POST"
        assert "unexpected-test-failure" not in record.getMessage()


class TestSensitiveInformation:
    def test_sensitive_information_is_not_exposed_by_application_log_formatter(self):
        logging_config = settings.LOGGING

        file_handler_config = logging_config["handlers"]["file"]
        formatter_name = file_handler_config["formatter"]
        formatter_config = logging_config["formatters"][formatter_name]

        formatter = logging.Formatter(
            formatter_config["format"],
            style=formatter_config.get("style", "%"),
        )

        logger = logging.getLogger("apps.security.audit")

        record = logger.makeRecord(
            logger.name,
            logging.INFO,
            __file__,
            1,
            "security_audit_event",
            (),
            None,
            extra={
                "event": "security_audit_event",
                "username": "test-user",
                "password": "TEST_PASSWORD",
                "api_key": "TEST_API_KEY",
                "token": "TEST_TOKEN",
                "credentials": "TEST_CREDENTIALS",
            },
        )

        formatted_log = formatter.format(record)

        assert "security_audit_event" in formatted_log

        for sensitive_value in (
            "TEST_PASSWORD",
            "TEST_API_KEY",
            "TEST_TOKEN",
            "TEST_CREDENTIALS",
        ):
            assert sensitive_value not in formatted_log


class TestM4RequestFailureLogging:
    @pytest.mark.django_db
    def test_validation_failure_emits_request_failure_log(
        self,
        operations_api_client,
        caplog,
    ):
        with caplog.at_level(logging.WARNING):
            response = operations_api_client.post(
                "/api/v1/orders/",
                {},
                format="json",
            )

        assert response.status_code == 400

        records = [
            record
            for record in caplog.records
            if record.__dict__.get("event") == "request_failure"
        ]

        assert records

        record = records[-1]
        assert record.levelno == logging.WARNING
        assert record.__dict__.get("failure_type") == "validation"
        assert record.__dict__.get("status_code") == 400
        assert record.__dict__.get("error_code") == "VALIDATION_ERROR"
        assert record.__dict__.get("method") == "POST"
        assert record.__dict__.get("view") == "OrderCreateView"
        assert record.__dict__.get("path") == "/api/v1/orders/"


class TestM4AuthenticationFailureLogging:
    def test_authentication_failure_emits_request_failure_log(
        self,
        client,
        caplog,
    ):
        with caplog.at_level(logging.WARNING):
            response = client.get("/api/v1/customers/")

        assert response.status_code == 401

        records = [
            record
            for record in caplog.records
            if record.__dict__.get("event") == "request_failure"
        ]

        assert records

        record = records[-1]
        assert record.levelno == logging.WARNING
        assert record.__dict__.get("failure_type") == "authentication"
        assert record.__dict__.get("status_code") == 401
        assert record.__dict__.get("method") == "GET"


class TestM4PermissionFailureLogging:
    @pytest.mark.django_db
    def test_permission_failure_emits_request_failure_log(
        self,
        read_only_api_client,
        caplog,
    ):
        with caplog.at_level(logging.WARNING):
            response = read_only_api_client.post(
                "/api/v1/orders/",
                {},
                format="json",
            )

        assert response.status_code == 403

        records = [
            record
            for record in caplog.records
            if record.__dict__.get("event") == "request_failure"
        ]

        assert records

        record = records[-1]
        assert record.levelno == logging.WARNING
        assert record.__dict__.get("failure_type") == "permission"
        assert record.__dict__.get("status_code") == 403
        assert record.__dict__.get("method") == "POST"


class TestM4BusinessFailureLogging:
    @pytest.mark.django_db
    def test_business_failure_emits_request_failure_log(
        self,
        operations_api_client,
        caplog,
    ):
        with caplog.at_level(logging.WARNING):
            response = operations_api_client.post(
                "/api/v1/orders/00000000-0000-0000-0000-000000000000/cancel/",
                {},
                format="json",
            )

        assert response.status_code == 404

        records = [
            record
            for record in caplog.records
            if record.__dict__.get("event") == "request_failure"
        ]

        assert records

        record = records[-1]
        assert record.levelno == logging.WARNING
        assert record.__dict__.get("failure_type") == "business"
        assert record.__dict__.get("status_code") == 404
        assert record.__dict__.get("error_code") == "ORDER_NOT_FOUND"
        assert record.__dict__.get("method") == "POST"


class TestM4MigrationFailureLogging:
    @pytest.mark.django_db
    def test_operational_migration_failure_emits_migration_failed_log(
        self,
        tmp_path,
        monkeypatch,
        caplog,
    ):
        from django.core.management import call_command

        import apps.customers.services as customer_services

        csv_file = tmp_path / "customers.csv"
        csv_file.write_text(
            "name,email,phone\n"
            "Test Customer,test@example.com,123456789\n",
            encoding="utf-8",
        )

        def raise_migration_failure(*args, **kwargs):
            raise RuntimeError("SECRET_MIGRATION_FAILURE")

        monkeypatch.setattr(
            customer_services.Customer.objects,
            "create",
            raise_migration_failure,
        )

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError):
                call_command(
                    "import_customers",
                    str(csv_file),
                )

        records = [
            record
            for record in caplog.records
            if record.__dict__.get("event") == "migration_failed"
        ]

        assert records

        record = records[-1]
        assert record.levelno == logging.ERROR
        assert record.__dict__.get("failure_type") == "operational"
        assert record.__dict__.get("exception_type") == "RuntimeError"
        assert "SECRET_MIGRATION_FAILURE" not in record.getMessage()


class TestM4MigrationValidationLogging:
    @pytest.mark.django_db
    def test_rejected_migration_row_is_not_logged_as_migration_failure(
        self,
        tmp_path,
        caplog,
    ):
        from django.core.management import call_command

        csv_file = tmp_path / "customers.csv"
        csv_file.write_text(
            "name,email,phone\n"
            ",invalid-email,123\n",
            encoding="utf-8",
        )

        with caplog.at_level(logging.ERROR):
            call_command(
                "import_customers",
                str(csv_file),
            )

        migration_failure_records = [
            record
            for record in caplog.records
            if record.__dict__.get("event") == "migration_failed"
        ]

        assert not migration_failure_records


class TestM4SensitiveOperationalLogging:
    @pytest.mark.django_db
    def test_request_failure_log_does_not_expose_request_data(
        self,
        operations_api_client,
        caplog,
    ):
        sensitive_value = "SECRET_REQUEST_VALUE"

        with caplog.at_level(logging.WARNING):
            response = operations_api_client.post(
                "/api/v1/orders/",
                {
                    "customer": sensitive_value,
                    "password": "SECRET_PASSWORD",
                    "token": "SECRET_TOKEN",
                },
                format="json",
            )

        assert response.status_code == 400

        records = [
            record
            for record in caplog.records
            if record.__dict__.get("event") == "request_failure"
        ]

        assert records

        formatted_logs = "\n".join(
            record.getMessage()
            for record in records
        )

        assert sensitive_value not in formatted_logs
        assert "SECRET_PASSWORD" not in formatted_logs
        assert "SECRET_TOKEN" not in formatted_logs
