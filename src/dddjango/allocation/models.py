from typing import Set
from django.db import models
from allocation.domain import model as domain_model


class Batch(models.Model):
    id = models.AutoField(primary_key=True)
    reference = models.CharField(max_length=255)
    sku = models.CharField(max_length=255)
    purchased_qty = models.IntegerField()
    eta = models.DateField(blank=True, null=True)

    class Meta:
        app_label = 'allocation'

    
    def to_domain(self) -> domain_model.Batch:

        domain_batch = domain_model.Batch(
            self.reference, self.sku, self.purchased_qty, self.eta
        )
        for line in Allocation.allocations_to_domain(self):
            domain_batch.allocate(line)

        return domain_batch


class Allocation(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255)
    sku = models.CharField(max_length=255)
    qty = models.IntegerField()

    class Meta:
        app_label = 'allocation'


    @staticmethod
    def allocations_to_domain(Batch) -> Set[domain_model.OrderLine]:
        return {
            domain_model.OrderLine(line.order_id, line.sku, line.qty)
            for line in Batch.allocation_set.all()
        }
