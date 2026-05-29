from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = 'Seed default users and tenant for demo and submission review'

    def handle(self, *args, **options):
        tenant, created = Tenant.objects.get_or_create(
            id=1,
            defaults={'name': 'Acme Corp', 'slug': 'acme-corp'},
        )
        if created:
            self.stdout.write('Created tenant: Acme Corp (id=1)')

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@carbonledger.demo',
                password='admin123',
            )
            self.stdout.write('Created superuser: admin / admin123')

        if not User.objects.filter(username='analyst').exists():
            User.objects.create_user(
                username='analyst',
                email='analyst@carbonledger.demo',
                password='analyst123',
                is_staff=False,
            )
            self.stdout.write('Created analyst user: analyst / analyst123')

        self.stdout.write(self.style.SUCCESS('Seed complete'))
