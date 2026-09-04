import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.customers.models import Customer


@pytest.mark.django_db
def test_import_customers_command_imports_csv_file(tmp_path):
    csv_file = tmp_path / "customers.csv"
    csv_file.write_text(
        """name,email,phone
Acme Ltd,contact@acme.example,+302101234567
Beta Stores,info@beta.example,+302109876543
""",
        encoding="utf-8",
    )

    call_command("import_customers", str(csv_file))

    assert Customer.objects.count() == 2
    assert Customer.objects.filter(name="Acme Ltd").exists()
    assert Customer.objects.filter(name="Beta Stores").exists()


@pytest.mark.django_db
def test_import_customers_command_reports_import_summary(
    tmp_path,
    capsys,
):
    csv_file = tmp_path / "customers.csv"
    csv_file.write_text(
        """name,email,phone
Valid Customer,valid@example.com,+302101234567
,,+302101234568
Another Valid Customer,another@example.com,
""",
        encoding="utf-8",
    )

    call_command("import_customers", str(csv_file))

    output = capsys.readouterr().out

    assert "Records processed: 3" in output
    assert "Records imported: 2" in output
    assert "Records rejected: 1" in output
    assert "row 3" in output.lower()
    assert "name" in output.lower()


@pytest.mark.django_db
def test_import_customers_command_fails_for_missing_file():
    with pytest.raises(CommandError):
        call_command(
            "import_customers",
            "/tmp/does-not-exist-customers.csv",
        )


@pytest.mark.django_db
def test_import_customers_command_does_not_import_invalid_rows(
    tmp_path,
):
    csv_file = tmp_path / "customers.csv"
    csv_file.write_text(
        """name,email,phone
,invalid@example.com,+302101234567
""",
        encoding="utf-8",
    )

    call_command("import_customers", str(csv_file))

    assert Customer.objects.count() == 0
