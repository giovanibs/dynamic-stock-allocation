from abc import ABC, abstractmethod
from typing import List, Set
from allocation.domain import model as domain_models
from allocation.domain.exceptions import InexistentProduct
from dddjango.alloc import models as django_models


class AbstractRepository(ABC):

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

    def add(self, product: domain_models.Product) -> None:
        super().add(product)
        django_product = django_models.Product.objects.create(sku=product.sku)
        self._add_batches(product.batches, django_product)

    
    def _add_batches(self, batches, django_product):
        for batch in batches:
            django_batch = django_models.Batch.objects.create(
                ref=batch.ref,
                product=django_product,
                qty=batch.available_qty + batch.allocated_qty,
                eta=batch.eta,
            )
            self._add_lines(batch.allocations, django_batch)

    
    @staticmethod
    def _add_lines(allocations, django_batch):
        for line in allocations:
            django_models.Allocation.objects.create(
                    batch = django_batch,
                    order_id=line.order_id,
                    sku=line.sku,
                    qty=line.qty,
                )


    def _get(self, sku) -> domain_models.Product:
        try:
            return django_models.Product.objects.get(sku=sku).to_domain()
        except django_models.Product.DoesNotExist:
            raise InexistentProduct


    def update(self, updated_product: domain_models.Product) -> None:
        # not using `get` here to prevent triggering update on uow commit
        current_domain_product = self._get(updated_product.sku)
        
        self._delete_removed_allocations_from_updated_product(
            updated_product.batches,
            current_domain_product.batches
        )
        self._create_new_allocations_from_updated_product(
            updated_product.batches,
            current_domain_product.batches
        )
        self._add_new_batches(
            updated_product.batches,
            current_domain_product.batches
        )


    def _delete_removed_allocations_from_updated_product(
            self,
            updated_batches: List[domain_models.Batch],
            current_batches: List[domain_models.Batch],
    ):
        for batch in current_batches:
            updated_batch = self._get_batch_by_ref(updated_batches, batch.ref)
            django_batch = django_models.Batch.objects.get(ref=batch.ref)
            removed_lines_order_id = {l.order_id for l in batch.allocations
                                      if l not in updated_batch.allocations}
            
            for line in django_batch.allocations.all():
                if line.order_id in removed_lines_order_id:
                    line.delete()
    
    
    def _create_new_allocations_from_updated_product(
            self,
            updated_batches: List[domain_models.Batch],
            current_batches: List[domain_models.Batch]
    ):
        for batch in current_batches:
            updated_batch = self._get_batch_by_ref(updated_batches, batch.ref)
            django_batch = django_models.Batch.objects.get(ref=batch.ref)
            new_lines = {l for l in updated_batch.allocations if l not in batch.allocations}
            self._add_lines(new_lines, django_batch)


    def _add_new_batches(
            self,
            updated_batches: List[domain_models.Batch],
            current_batches: List[domain_models.Batch],
    ):
        current_batches_ref = {b.ref for b in current_batches}
        updated_batches_ref = {b.ref for b in updated_batches}
        new_batches_ref = updated_batches_ref - current_batches_ref
        
        if new_batches_ref:
            django_product = django_models.Product.objects.get(sku=updated_batches[0].sku)
        
        for batch_ref in new_batches_ref:
            self._add_batches(
                [self._get_batch_by_ref(updated_batches, batch_ref)],
                django_product
            )


    @staticmethod
    def _get_batch_by_ref(batches, ref: str):
        return next(batch for batch in batches if batch.ref == ref)

    
    def list(self) -> List[domain_models.Product]:
        return [p.to_domain() for p in django_models.Product.objects.all()]
