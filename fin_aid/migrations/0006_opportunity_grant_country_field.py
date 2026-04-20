# Generated manually for CountryField + data copy from legacy text

import django_countries.fields
from django.db import migrations


def copy_country_from_legacy_text(apps, schema_editor):
    OpportunityGrantApplication = apps.get_model('fin_aid', 'OpportunityGrantApplication')
    from django_countries import countries

    name_to_code = {name.lower(): code for code, name in countries}
    aliases = {
        'uk': 'GB',
        'usa': 'US',
        'u.s.a.': 'US',
        'uae': 'AE',
    }
    for obj in OpportunityGrantApplication.objects.all():
        raw = getattr(obj, 'country_or_region', None) or ''
        text = str(raw).strip()
        if not text:
            obj.country = 'UG'
            obj.save(update_fields=['country'])
            continue
        key = text.lower()
        code = name_to_code.get(key) or aliases.get(key)
        if not code:
            for name, c in name_to_code.items():
                if key in name or name in key:
                    code = c
                    break
        obj.country = code or 'UG'
        obj.save(update_fields=['country'])


class Migration(migrations.Migration):

    dependencies = [
        ('fin_aid', '0005_remove_fin_aid_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='opportunitygrantapplication',
            name='country',
            field=django_countries.fields.CountryField(
                blank_label='(select country)',
                max_length=2,
                null=True,
            ),
        ),
        migrations.RunPython(copy_country_from_legacy_text, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='opportunitygrantapplication',
            name='country_or_region',
        ),
        migrations.AlterField(
            model_name='opportunitygrantapplication',
            name='country',
            field=django_countries.fields.CountryField(
                'Country',
                blank_label='(select country)',
                max_length=2,
            ),
        ),
    ]
