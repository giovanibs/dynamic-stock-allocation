from typing import Set
from django.db import models
from allocation.domain import model as domain_model


class Product(models.Model):
    sku = models.CharField(max_length=255, primary_key=True)

    class Meta:
        app_label = 'alloc'
    
    
    def to_domain(self) -> domain_model.Product:
        return domain_model.Product(
            self.sku,
            [batch.to_domain() for batch in self.batches.all()]
        )


class Batch(models.Model):
    reference = models.CharField(max_length=255, primary_key=True)
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE, related_name='batches')
    purchased_qty = models.IntegerField()
    eta = models.DateField(blank=True, null=True)

    class Meta:
        app_label = 'alloc'

    
    def to_domain(self) -> domain_model.Batch:

        domain_batch = domain_model.Batch(
            self.reference, self.product.sku, self.purchased_qty, self.eta
        )
        for line in Allocation.allocations_to_domain(self):
            domain_batch.allocate(line)

        return domain_batch


class Allocation(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, related_name='allocations')
    order_id = models.CharField(max_length=255)
    sku = models.CharField(max_length=255)
    qty = models.IntegerField()

    class Meta:
        app_label = 'alloc'


    @staticmethod
    def allocations_to_domain(Batch) -> Set[domain_model.OrderLine]:
        return {
            domain_model.OrderLine(line.order_id, line.sku, line.qty)
            for line in Batch.allocations.all()
        }
