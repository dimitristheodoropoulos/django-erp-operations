import pytest

from apps.customers.models import Customer


@pytest.mark.django_db
def test_customer_imports_valid_csv_rows():
    from apps.customers.services import import_customers

    csv_content = """name,email,phone
Acme Ltd,contact@acme.example,+302101234567
Beta Stores,info@beta.example,+302109876543
"""

    report = import_customers(csv_content)

    assert report.records_processed == 2
    assert report.records_imported == 2
    assert report.records_rejected == 0
    assert report.validation_errors == []

    assert Customer.objects.count() == 2

    acme = Customer.objects.get(name="Acme Ltd")
    assert acme.email == "contact@acme.example"
    assert acme.phone == "+302101234567"
    assert acme.active is True


@pytest.mark.django_db
def test_customer_import_transforms_whitespace_and_empty_optional_values():
    from apps.customers.services import import_customers

    csv_content = """name,email,phone
  Acme Ltd  ,  contact@acme.example  ,
"""

    report = import_customers(csv_content)

    assert report.records_processed == 1
    assert report.records_imported == 1
    assert report.records_rejected == 0

    customer = Customer.objects.get()

    assert customer.name == "Acme Ltd"
    assert customer.email == "contact@acme.example"
    assert customer.phone is None


@pytest.mark.django_db
def test_customer_import_rejects_blank_name():
    from apps.customers.services import import_customers

    csv_content = """name,email,phone
,invalid@example.com,+302101234567
"""

    report = import_customers(csv_content)

    assert report.records_processed == 1
    assert report.records_imported == 0
    assert report.records_rejected == 1

    assert Customer.objects.count() == 0

    assert len(report.validation_errors) == 1
    assert report.validation_errors[0]["row"] == 2
    assert report.validation_errors[0]["field"] == "name"


@pytest.mark.django_db
def test_customer_import_rejects_name_longer_than_customer_limit():
    from apps.customers.services import import_customers

    long_name = "A" * 256

    csv_content = f"""name,email,phone
{long_name},customer@example.com,+302101234567
"""

    report = import_customers(csv_content)

    assert report.records_processed == 1
    assert report.records_imported == 0
    assert report.records_rejected == 1

    assert Customer.objects.count() == 0

    assert report.validation_errors[0]["row"] == 2
    assert report.validation_errors[0]["field"] == "name"


@pytest.mark.django_db
def test_customer_import_rejects_email_longer_than_customer_limit():
    from apps.customers.services import import_customers

    long_email = ("a" * 245) + "@example.com"

    csv_content = f"""name,email,phone
Customer,{long_email},+302101234567
"""

    report = import_customers(csv_content)

    assert report.records_processed == 1
    assert report.records_imported == 0
    assert report.records_rejected == 1

    assert Customer.objects.count() == 0

    assert report.validation_errors[0]["row"] == 2
    assert report.validation_errors[0]["field"] == "email"


@pytest.mark.django_db
def test_customer_import_rejects_phone_longer_than_customer_limit():
    from apps.customers.services import import_customers

    long_phone = "1" * 33

    csv_content = f"""name,email,phone
Customer,customer@example.com,{long_phone}
"""

    report = import_customers(csv_content)

    assert report.records_processed == 1
    assert report.records_imported == 0
    assert report.records_rejected == 1

    assert Customer.objects.count() == 0

    assert report.validation_errors[0]["row"] == 2
    assert report.validation_errors[0]["field"] == "phone"


@pytest.mark.django_db
def test_customer_import_allows_partial_success():
    from apps.customers.services import import_customers

    csv_content = """name,email,phone
Valid Customer,valid@example.com,+302101234567
,,+302101234568
Another Valid Customer,another@example.com,
"""

    report = import_customers(csv_content)

    assert report.records_processed == 3
    assert report.records_imported == 2
    assert report.records_rejected == 1

    assert Customer.objects.count() == 2
    assert Customer.objects.filter(name="Valid Customer").exists()
    assert Customer.objects.filter(name="Another Valid Customer").exists()

    assert len(report.validation_errors) == 1
    assert report.validation_errors[0]["row"] == 3
    assert report.validation_errors[0]["field"] == "name"


@pytest.mark.django_db
def test_customer_import_report_contains_diagnostic_validation_message():
    from apps.customers.services import import_customers

    csv_content = """name,email,phone
,broken@example.com,+302101234567
"""

    report = import_customers(csv_content)

    error = report.validation_errors[0]

    assert error["row"] == 2
    assert error["field"] == "name"
    assert error["message"]


@pytest.mark.django_db
def test_customer_import_does_not_use_csv_id_or_timestamps():
    from apps.customers.services import import_customers

    csv_content = """name,email,phone
Customer,customer@example.com,+302101234567
"""

    report = import_customers(csv_content)

    assert report.records_imported == 1

    customer = Customer.objects.get()

    assert customer.id is not None
    assert customer.created_at is not None
    assert customer.modified_at is not None
    assert customer.active is True
