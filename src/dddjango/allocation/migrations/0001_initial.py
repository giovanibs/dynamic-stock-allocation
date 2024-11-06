# Generated by Django 5.1.3 on 2024-11-06 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=255)),
                ('sku', models.CharField(max_length=255)),
                ('purchased_qty', models.IntegerField()),
                ('eta', models.DateField(blank=True, null=True)),
            ],
        ),
    ]