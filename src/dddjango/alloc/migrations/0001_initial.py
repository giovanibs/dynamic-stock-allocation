# Generated by Django 5.1.3 on 2024-11-12 18:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('ref', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('qty', models.IntegerField()),
                ('eta', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('sku', models.CharField(max_length=255, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Allocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=255)),
                ('sku', models.CharField(max_length=255)),
                ('qty', models.IntegerField()),
                ('batch', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='allocations', to='alloc.batch')),
            ],
        ),
        migrations.AddField(
            model_name='batch',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batches', to='alloc.product'),
        ),
    ]
