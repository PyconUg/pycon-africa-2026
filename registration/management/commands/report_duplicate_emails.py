from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models.functions import Lower


class Command(BaseCommand):
    help = "Report duplicate user emails (read-only audit for ops)."

    def handle(self, *args, **options):
        User = get_user_model()
        duplicates = (
            User.objects.exclude(email="")
            .annotate(lower_email=Lower("email"))
            .values("lower_email")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
            .order_by("lower_email")
        )

        if not duplicates:
            self.stdout.write(self.style.SUCCESS("No duplicate emails found."))
            return

        self.stdout.write(self.style.WARNING("Duplicate emails found:"))
        for row in duplicates:
            email = row["lower_email"]
            users = User.objects.filter(email__iexact=email).order_by("date_joined")
            self.stdout.write(f"\n  {email} ({row['count']} accounts):")
            for user in users:
                active = "active" if user.is_active else "inactive"
                self.stdout.write(
                    f"    id={user.pk} username={user.username!r} "
                    f"joined={user.date_joined:%Y-%m-%d} {active}"
                )
