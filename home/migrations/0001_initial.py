from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PyConEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('country', models.CharField(max_length=255)),
                ('flag_image', models.ImageField(default='flag.jpg', upload_to='countryflags/')),
                ('city', models.CharField(blank=True, max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('year', models.IntegerField()),
                ('website_url', models.URLField(blank=True)),
            ],
            options={
                'ordering': ['start_date'],
            },
        ),
        migrations.CreateModel(
            name='EventYear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(unique=True)),
                ('home_info', models.TextField(blank=True, null=True)),
                ('template_path', models.CharField(default='home/home.html', help_text="Path to the year's templates, e.g., '2020/home/home.html'", max_length=255)),
            ],
            options={
                'verbose_name': 'Event Year',
                'verbose_name_plural': 'Event Years',
            },
        ),
    ]
