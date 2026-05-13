from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("talks", "0003_reviewer_is_active_reviewer_review_load_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="proposal",
            name="last_program_status_email_sent_at",
            field=models.DateTimeField(
                blank=True,
                help_text="When the last programme status notification email was sent (accepted/waiting/rejected/submitted).",
                null=True,
            ),
        ),
    ]
