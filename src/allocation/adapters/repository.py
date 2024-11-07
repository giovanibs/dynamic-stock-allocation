from abc import ABC, abstractmethod
from typing import List
from allocation.domain import model as domain_models
from dddjango.allocation import models as django_models


class AbstractRepository(ABC):

    @abstractmethod
    def add(self, batch: domain_models.Batch) -> None:
        raise NotImplementedError()


    @abstractmethod
    def get(self, reference) -> domain_models.Batch:
        raise NotImplementedError()
    

    @abstractmethod
    def update(self, batch: domain_models.Batch) -> None:
        raise NotImplementedError()
    

    @abstractmethod
    def list(self) -> List[domain_models.Batch]:
        raise NotImplementedError()
    

class DjangoRepository(AbstractRepository):

    def add(self, batch: domain_models.Batch) -> None:
        
        django_batch = django_models.Batch(**batch.properties_dict)
        django_batch.save()
        for line in batch._allocations:
            django_models.Allocation.objects.create(
                batch=django_batch, order_id=line.order_id, sku=line.sku, qty=line.qty
            )
    
    def get(self, reference) -> domain_models.Batch:
        return django_models.Batch.objects.get(reference=reference).to_domain()
    

    def update(self, batch: domain_models.Batch) -> None:
        try:
            django_batch = django_models.Batch.objects.get(reference=batch.reference)
        except django_models.Batch.DoesNotExist:
            self.add(batch)
            return

        django_batch.sku = batch.sku
        django_batch.purchased_qty = batch.available_qty + batch.allocated_qty
        django_batch.eta = batch.eta
        django_batch.save()
        self._update_allocation_set(batch, django_batch)
        

    def _update_allocation_set(self, batch, django_batch):
        previous_allocation_set = list(django_batch.allocation_set.get_queryset())

        new_allocation_set = list(
            django_models.Allocation.objects.get_or_create(
                batch=django_batch,
                order_id=line.order_id,
                sku=line.sku,
                qty=line.qty
            )[0]
            for line in batch._allocations
        )
        django_batch.allocation_set.set(new_allocation_set)
        current_allocation_set = list(django_batch.allocation_set.get_queryset())
        for line in previous_allocation_set:
            if line not in current_allocation_set:
                line.delete()


    def list(self) -> List[domain_models.Batch]:
        return super().list()
