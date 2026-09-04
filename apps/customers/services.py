import csv
from dataclasses import dataclass, field
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from apps.customers.models import Customer


@dataclass
class CustomerImportReport:
    records_processed: int = 0
    records_imported: int = 0
    records_rejected: int = 0
    validation_errors: list[dict] = field(default_factory=list)


def _clean_optional(value):
    value = value.strip()
    return value or None


def _transform_row(row):
    return {
        "name": row["name"].strip(),
        "email": _clean_optional(row["email"]),
        "phone": _clean_optional(row["phone"]),
    }


def _validate_row(data):
    errors = []

    name = data["name"]
    email = data["email"]
    phone = data["phone"]

    if not name:
        errors.append(
            {
                "field": "name",
                "message": "This field may not be blank.",
            }
        )
    elif len(name) > 255:
        errors.append(
            {
                "field": "name",
                "message": "Ensure this value has at most 255 characters.",
            }
        )

    if email:
        if len(email) > 254:
            errors.append(
                {
                    "field": "email",
                    "message": "Ensure this value has at most 254 characters.",
                }
            )
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append(
                    {
                        "field": "email",
                        "message": "Enter a valid email address.",
                    }
                )

    if phone and len(phone) > 32:
        errors.append(
            {
                "field": "phone",
                "message": "Ensure this value has at most 32 characters.",
            }
        )

    return errors


def import_customers(csv_content):
    report = CustomerImportReport()

    reader = csv.DictReader(StringIO(csv_content))

    for row_number, row in enumerate(reader, start=2):
        report.records_processed += 1

        data = _transform_row(row)
        errors = _validate_row(data)

        if errors:
            report.records_rejected += 1

            for error in errors:
                report.validation_errors.append(
                    {
                        "row": row_number,
                        "field": error["field"],
                        "message": error["message"],
                    }
                )

            continue

        Customer.objects.create(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
        )

        report.records_imported += 1

    return report
