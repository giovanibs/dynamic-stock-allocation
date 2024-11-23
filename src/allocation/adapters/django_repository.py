from typing import List
from allocation.domain import model as domain_
from allocation.domain.exceptions import InexistentProduct
from allocation.domain.ports import AbstractWriteRepository
from dddjango.alloc import models as orm


class DjangoRepository(AbstractWriteRepository):

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
            removed_lines_order_id = {line.order_id for line in batch.allocations
                                      if line not in updated_batch.allocations}
            
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
            new_lines = {line for line in updated_batch.allocations
                         if line not in batch.allocations}
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
