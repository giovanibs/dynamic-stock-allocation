from abc import ABC, abstractmethod
from typing import List, Set
from allocation.domain import model as domain_models
from allocation.domain.exceptions import BatchDoesNotExist
from dddjango.alloc import models as django_models


class AbstractRepository(ABC):

    def __init__(self) -> None:
        self._seen: Set[domain_models.Batch] = set()


    @property
    def seen(self):
        return self._seen


    @abstractmethod
    def add(self, batch: domain_models.Batch) -> None:
        self._seen.add(batch)


    def get(self, reference) -> domain_models.Batch:
        batch = self._get(reference)
        self._seen.add(batch)
        return batch
    

    @abstractmethod
    def _get(self, reference) -> domain_models.Batch:
        raise NotImplementedError()
    

    @abstractmethod
    def update(self, batch: domain_models.Batch) -> None:
        raise NotImplementedError()
    

    @abstractmethod
    def list(self) -> List[domain_models.Batch]:
        raise NotImplementedError()


class AbstractProductRepository(ABC):

    def __init__(self) -> None:
        self._seen: Set[domain_models.Product] = set()


    @property
    def seen(self):
        return self._seen


    @abstractmethod
    def add(self, product: domain_models.Product) -> None:
        self._seen.add(product)


    def get(self, sku) -> domain_models.Product:
        product = self._get(sku)
        self._seen.add(product)
        return product
    

    @abstractmethod
    def _get(self, sku) -> domain_models.Product:
        raise NotImplementedError()
    

    @abstractmethod
    def update(self, product: domain_models.Product) -> None:
        raise NotImplementedError()
    

    @abstractmethod
    def list(self) -> List[domain_models.Product]:
        raise NotImplementedError()
    

class DjangoRepository(AbstractRepository):

    def add(self, batch: domain_models.Batch) -> None:
        super().add(batch)
        django_batch = django_models.Batch(**batch.properties_dict)
        django_batch.save()

        for line in batch._allocations:
            django_models.Allocation.objects.create(
                batch=django_batch, order_id=line.order_id, sku=line.sku, qty=line.qty
            )
    
    def _get(self, reference) -> domain_models.Batch:
        try:
            return django_models.Batch.objects.get(reference=reference).to_domain()
        except django_models.Batch.DoesNotExist:
            raise BatchDoesNotExist()


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
        batches = django_models.Batch.objects.all()
        return [batch.to_domain() for batch in batches]


class DjangoProductRepository(AbstractProductRepository):

    def add(self, product: domain_models.Product) -> None:
        super().add(product)
        django_product = django_models.Product.objects.create(sku=product.sku)
        self._add_batches(product.batches, django_product)

    
    def _add_batches(self, batches, django_product):
        for batch in batches:
            django_batch = django_models.Batch.objects.create(
                reference=batch.reference,
                product=django_product,
                purchased_qty=batch.available_qty + batch.allocated_qty,
                eta=batch.eta,
            )
            self._add_lines(batch.allocations, django_batch)

    
    def _add_lines(self, allocations, django_batch):
        for line in allocations:
            django_models.Allocation.objects.create(
                    batch = django_batch,
                    order_id=line.order_id,
                    sku=line.sku,
                    qty=line.qty,
                )


    def _get(self, sku) -> domain_models.Product:
        return super()._get(sku)
    

    def update(self, product: domain_models.Product) -> None:
        return super().update(product)
    

    def list(self) -> List[domain_models.Product]:
        return super().list()
