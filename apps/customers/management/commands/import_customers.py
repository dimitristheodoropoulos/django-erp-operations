from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.customers.services import import_customers


class Command(BaseCommand):
    help = "Import legacy customers from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            help="Path to the customer CSV file.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_file"])

        if not csv_path.is_file():
            raise CommandError(
                f"CSV file not found: {csv_path}"
            )

        try:
            csv_content = csv_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CommandError(
                f"Unable to read CSV file: {csv_path}"
            ) from exc

        report = import_customers(csv_content)

        self.stdout.write(
            f"Records processed: {report.records_processed}"
        )
        self.stdout.write(
            f"Records imported: {report.records_imported}"
        )
        self.stdout.write(
            f"Records rejected: {report.records_rejected}"
        )

        if report.validation_errors:
            self.stdout.write("Validation errors:")

            for error in report.validation_errors:
                self.stdout.write(
                    f"  Row {error['row']}, "
                    f"field '{error['field']}': "
                    f"{error['message']}"
                )
