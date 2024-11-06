from django.db import models


class Batch(models.Model):
    reference = models.CharField(max_length=255)
    sku = models.CharField(max_length=255)
    purchased_qty = models.IntegerField()
    eta = models.DateField(blank=True, null=True)

    class Meta:
        app_label = 'allocation'
