from django.db import models
from src.allocation.domain import model as domain_model


class Batch(models.Model):
    reference = models.CharField(max_length=255)
    sku = models.CharField(max_length=255)
    purchased_qty = models.IntegerField()
    eta = models.DateField(blank=True, null=True)


    class Meta:
        app_label = 'allocation'

    
    def to_domain(self):
        return domain_model.Batch(
            self.reference, self.sku, self.purchased_qty, self.eta
        )