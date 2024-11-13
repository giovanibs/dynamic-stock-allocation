from abc import ABC, abstractmethod
from typing import List, Set
from allocation.domain import model as domain_
from allocation.domain.exceptions import InexistentProduct
from dddjango.alloc import models as orm


class AbstractRepository(ABC):

    def __init__(self) -> None:
        self._seen: Set[domain_.Product] = set()


    @property
    def seen(self):
        return self._seen


    @abstractmethod
    def add(self, product: domain_.Product) -> None:
        self._seen.add(product)


    def get(self, sku) -> domain_.Product:
        # first check if product is already in self._seen to prevent overwriting
        # uncommited changes by refetching it from the DB
        product = next((p for p in self._seen if p.sku == sku), None)
        if product is None:
            product = self._get(sku)
            self._seen.add(product)
        return product
    

    @abstractmethod
    def _get(self, sku) -> domain_.Product:
        raise NotImplementedError()
    

    @abstractmethod
    def update(self, product: domain_.Product) -> None:
        raise NotImplementedError()
    

    @abstractmethod
    def list(self) -> List[domain_.Product]:
        raise NotImplementedError()
    

    def get_by_batch_ref(self, ref: str):
        # first check if product is already in self._seen to prevent overwriting
        # uncommited changes by refetching it from the DB
        product_in_seen = next(
            (p for p in self.seen for b in p.batches if b.ref == ref),
            None
        )
        if product_in_seen is not None:
            return product_in_seen
        
        product = self._get_by_batch_ref(ref)
        
        if product is None:
            return None
        
        self._seen.add(product)
        return product
    

    @abstractmethod
    def _get_by_batch_ref(self, ref):
        raise NotImplemented


class DjangoRepository(AbstractRepository):

    def add(self, product: domain_.Product) -> None:
        super().add(product)
        orm_product = orm.Product.objects.create(sku=product.sku)
        self._add_batches(product.batches, orm_product)

    
    def _add_batches(self, batches, orm_product):
        for batch in batches:
            orm_batch = orm.Batch.objects.create(
                ref=batch.ref,
                product=orm_product,
                qty=batch.available_qty + batch.allocated_qty,
                eta=batch.eta,
            )
            self._add_lines(batch.allocations, orm_batch)

    
    @staticmethod
    def _add_lines(allocations, orm_batch):
        for line in allocations:
            orm.Allocation.objects.create(
                    batch = orm_batch,
                    order_id=line.order_id,
                    sku=line.sku,
                    qty=line.qty,
                )


    def _get(self, sku) -> domain_.Product:
        try:
            return orm.Product.objects.get(sku=sku).to_domain()
        except orm.Product.DoesNotExist:
            raise InexistentProduct


    def update(self, updated_product: domain_.Product) -> None:
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
            updated_batches: List[domain_.Batch],
            current_batches: List[domain_.Batch],
    ):
        for batch in current_batches:
            updated_batch = self._get_batch_by_ref(updated_batches, batch.ref)
            orm_batch = orm.Batch.objects.get(ref=batch.ref)
            removed_lines_order_id = {l.order_id for l in batch.allocations
                                      if l not in updated_batch.allocations}
            
            for line in orm_batch.allocations.all():
                if line.order_id in removed_lines_order_id:
                    line.delete()
    
    
    def _create_new_allocations_from_updated_product(
            self,
            updated_batches: List[domain_.Batch],
            current_batches: List[domain_.Batch]
    ):
        for batch in current_batches:
            updated_batch = self._get_batch_by_ref(updated_batches, batch.ref)
            orm_batch = orm.Batch.objects.get(ref=batch.ref)
            new_lines = {l for l in updated_batch.allocations if l not in batch.allocations}
            self._add_lines(new_lines, orm_batch)


    def _add_new_batches(
            self,
            updated_batches: List[domain_.Batch],
            current_batches: List[domain_.Batch],
    ):
        current_batches_ref = {b.ref for b in current_batches}
        updated_batches_ref = {b.ref for b in updated_batches}
        new_batches_ref = updated_batches_ref - current_batches_ref
        
        if new_batches_ref:
            orm_product = orm.Product.objects.get(sku=updated_batches[0].sku)
        
        for batch_ref in new_batches_ref:
            self._add_batches(
                [self._get_batch_by_ref(updated_batches, batch_ref)],
                orm_product
            )


    @staticmethod
    def _get_batch_by_ref(batches, ref: str):
        return next(batch for batch in batches if batch.ref == ref)

    
    def list(self) -> List[domain_.Product]:
        return [p.to_domain() for p in orm.Product.objects.all()]
    

    def _get_by_batch_ref(self, ref):
        products = self.list()
        return next(
            (p for p in products for b in p.batches if b.ref == ref),
            None
        )
