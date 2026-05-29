from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from apps.tenants.models import Tenant
from apps.ingestion.models import IngestionBatch, RawRecord
from apps.emissions.models import NormalizedEmission
from apps.ingestion.parsers.sap import parse as parse_sap
from apps.ingestion.parsers.utility import parse as parse_utility
from apps.ingestion.parsers.travel import parse as parse_travel

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / 'sample_data'

SOURCES = [
    ('sap',     'sap_export.csv',     parse_sap),
    ('utility', 'utility_bill.csv',   parse_utility),
    ('travel',  'travel_export.csv',  parse_travel),
]


class Command(BaseCommand):
    help = 'Seed default users, tenant, and sample emissions data'

    def handle(self, *args, **options):
        tenant, created = Tenant.objects.get_or_create(
            id=1,
            defaults={'name': 'Acme Corp', 'slug': 'acme-corp'},
        )
        if created:
            self.stdout.write('Created tenant: Acme Corp (id=1)')

        admin = None
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@carbonledger.demo',
                password='admin123',
            )
            self.stdout.write('Created superuser: admin / admin123')
        else:
            admin = User.objects.get(username='admin')

        if not User.objects.filter(username='analyst').exists():
            User.objects.create_user(
                username='analyst',
                email='analyst@carbonledger.demo',
                password='analyst123',
            )
            self.stdout.write('Created analyst user: analyst / analyst123')

        if NormalizedEmission.objects.filter(tenant=tenant).exists():
            self.stdout.write('Sample data already loaded, skipping')
            self.stdout.write(self.style.SUCCESS('Seed complete'))
            return

        for source, filename, parse_fn in SOURCES:
            csv_path = SAMPLE_DIR / filename
            if not csv_path.exists():
                self.stdout.write(self.style.WARNING(f'Sample file not found: {csv_path}, skipping'))
                continue

            content = csv_path.read_text(encoding='utf-8')
            result = parse_fn(content)

            with transaction.atomic():
                batch = IngestionBatch.objects.create(
                    tenant=tenant,
                    source=source,
                    uploaded_by=admin,
                    original_filename=filename,
                    total_rows=len(result['success']) + len(result['failed']),
                    parsed_rows=len(result['success']),
                    failed_rows=len(result['failed']),
                )

                for row in result['success']:
                    raw = RawRecord.objects.create(
                        batch=batch,
                        row_number=row['row'],
                        raw_payload=row['raw'],
                    )
                    row_status = NormalizedEmission.STATUS_PENDING
                    flag_reason = ''
                    if row.get('warnings'):
                        row_status = NormalizedEmission.STATUS_FLAGGED
                        flag_reason = '; '.join(w['msg'] for w in row['warnings'])

                    NormalizedEmission.objects.create(
                        tenant=tenant,
                        batch=batch,
                        raw_record=raw,
                        scope=row['scope'],
                        source=row['source'],
                        activity_date=row['activity_date'],
                        description=row.get('description', ''),
                        location=row.get('location', ''),
                        original_value=row['original_value'],
                        original_unit=row['original_unit'],
                        normalized_value=row['normalized_value'],
                        normalized_unit=row['normalized_unit'],
                        co2e_kg=row['co2e_kg'],
                        status=row_status,
                        flag_reason=flag_reason,
                    )

                for row in result['failed']:
                    RawRecord.objects.create(
                        batch=batch,
                        row_number=row['row'],
                        raw_payload=row['raw'],
                        parse_error=row['error'],
                    )

            self.stdout.write(
                f'Loaded {source}: {len(result["success"])} rows parsed, {len(result["failed"])} failed'
            )

        self.stdout.write(self.style.SUCCESS('Seed complete'))
