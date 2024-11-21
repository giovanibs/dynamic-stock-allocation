from typing import List, Optional
import pytest
from allocation.domain import commands, events
from allocation.domain.exceptions import (
    InexistentProduct, LineIsNotAllocatedError, OutOfStock
)
from allocation.domain.model import Product
from allocation.domain.ports import (
    AbstractPublisher, AbstractQueryRepository, AbstractWriteRepository
)
from allocation.orchestration import bootstrapper
from allocation.orchestration.uow import AbstractUnitOfWork
from dddjango.alloc.models import Product


class FakeWriteRepository(AbstractWriteRepository):

        def __init__(self, products: Optional[List[Product]] = None) -> None:
            super().__init__()
            self._products = set(products) if products is not None else set()


        def get(self, sku) -> Product:
            product = self._get(sku)
            self._seen.add(product)
            return product


        def _get(self, sku: str) -> Product:
            try:
                return next(product
                            for product in self._products
                            if product.sku == sku)
            except StopIteration:
                raise InexistentProduct('Product does not exist.')


        def add(self, product: Product) -> None:
            self._products.add(product)


        def update(self, product) -> None:
            old_product = self.get(product.sku)
            self._products.remove(old_product)
            self.add(product)


        def list(self):
            return list(self._products)
        
    
        def _get_by_batch_ref(self, ref):
            products = self.list()
            return next(
                (p for p in products for b in p.batches if b.ref == ref),
                None
            )


class FakeQueryRepo(AbstractQueryRepository):
    def add_batch(self, *args, **kwargs): ...
    def get_batch(self, *args, **kwargs): ...
    def update_batch_quantity(self, *args, **kwargs): ...
    def add_allocation_for_line(self, *args, **kwargs): ...
    def get_allocation_for_line(self, *args, **kwargs): ...
    def remove_allocation_for_line(self, *args, **kwargs): ...
    def add_allocation_for_order(self, *args, **kwargs): ...
    def get_allocations_for_order(self, *args, **kwargs): ...
    def remove_allocation_for_order(self, *args, **kwargs): ...


class FakePublisher(AbstractPublisher):
    def publish_event(*args, **kwargs): ...


class FakeProductUoW(AbstractUnitOfWork):

        def __init__(
                self,
                repo: AbstractWriteRepository,
        ) -> None:
            self._products = repo
            self._commited = False
            self.collected_messages = []


        @property
        def commited(self) -> bool:
            return self._commited
        

        @property
        def products(self) -> AbstractWriteRepository:
            return self._products
        
        
        def __enter__(self) -> AbstractUnitOfWork:
            self._commited = False
            return super().__enter__()
        

        def __exit__(self, *args) -> None:
            return super().__exit__(*args)


        def _commit(self):
            self._collect_messages()

            if events.OutOfStock in {type(msg) for msg in self.collected_messages}:
                return
            
            self._commited = True

        def _collect_messages(self):
            for product in self.products.seen:
                if product.messages:
                    self.collected_messages.extend(product.messages)


        def rollback(self):
            self._collect_messages()


@pytest.fixture
def uow():
    return FakeProductUoW(FakeWriteRepository())


@pytest.fixture
def bus(uow):
    return bootstrapper.bootstrap(
        uow=uow,
        publisher=FakePublisher(),
        query_repository=FakeQueryRepo()
    )


@pytest.fixture
def batch(tomorrow):
    return ('batch', 'skew', 10, tomorrow)


class TestOrchestrationAddBatch:

    def test_can_add_a_batch(self, batch, uow, bus):
        bus.handle(commands.CreateBatch(*batch))
        product = uow.products.get(batch[1])
        assert batch[0] in {b.ref for b in product.batches}
        assert uow.commited


    def test_adding_a_batch_also_adds_a_new_product(self, batch, uow, bus):
        with pytest.raises(InexistentProduct):
            uow.products.get(batch[1])

        bus.handle(commands.CreateBatch(*batch))
        product = uow.products.get(batch[1])
        assert batch[0] in {b.ref for b in product.batches}


class TestOrchestrationAllocate:

    def test_allocate_commits_on_happy_path(self, batch, uow, bus):
        bus.handle(commands.CreateBatch(*batch))
        line = ('o1', 'skew', 1)
        
        bus.handle(commands.Allocate(*line))
        assert uow.commited == True


    def test_allocate_returns_batch_ref(self, today, later, bus):
        earlier_batch = ('earlier', 'skew', 10, today)
        later_batch = ('later', 'skew', 10, later)
        bus.handle(commands.CreateBatch(*earlier_batch))
        bus.handle(commands.CreateBatch(*later_batch))
        line = ('o1', 'skew', 1)
        
        results = bus.handle(commands.Allocate(*line))
        assert results[-1] == earlier_batch[0]
    

    def test_allocate_decreases_the_available_qty(self, uow, bus):
        bus.handle(commands.CreateBatch('batch', 'skew', 10))
        line = ('o1', 'skew', 10)
        bus.handle(commands.Allocate(*line))
        assert uow.products.get(sku='skew').batches[0].available_qty == 0


    @pytest.mark.parametrize(
        ('line', 'expected_exception'),
        [
            (('o1', 'invalid_skew', 1), InexistentProduct),
            (('o2', 'skew', 1_000), OutOfStock),
        ]
    )
    def test_allocate_raises_errors_and_do_not_commit(
        self, batch, bus, uow, line, expected_exception
    ):
        bus.handle(commands.CreateBatch(*batch))
        
        with pytest.raises(expected_exception):
            bus.handle(commands.Allocate(*line))
        
        assert uow.commited == False
    

class TestOrchestrationDeallocate:

    def test_deallocate_returns_batch_ref(self, bus):
        batch_with_the_line = ('it_is_me', 'skew', 10, None)
        batch_without_the_line = ('it_is_not_me', 'skew', 1, None)
        bus.handle(commands.CreateBatch(*batch_with_the_line))
        bus.handle(commands.CreateBatch(*batch_without_the_line))
        line = ('o1', 'skew', 10)
        bus.handle(commands.Allocate(*line))
        results = bus.handle(commands.Deallocate(*line))
        assert results[0] == batch_with_the_line[0]
    

    def test_deallocate_decreases_the_allocated_qty(self, uow, bus):
        bus.handle(commands.CreateBatch('batch', 'skew', 10))
        line = ('o1', 'skew', 10)
        bus.handle(commands.Allocate(*line))
        bus.handle(commands.Deallocate(*line))
        
        assert uow.products.get(sku='skew').batches[0].allocated_qty == 0


    def test_deallocate_commits_on_happy_path(self, batch, uow, bus):
        bus.handle(commands.CreateBatch(*batch))
        line = ('o1', 'skew', 1)
        bus.handle(commands.Allocate(*line))
        
        bus.handle(commands.Deallocate(*line))
        assert uow.commited == True


    @pytest.mark.parametrize(
        ('line', 'expected_exception'),
        [
            (('o1', 'invalid_skew', 1), InexistentProduct),
            (('o2', 'skew', 1), LineIsNotAllocatedError),
        ]
    )
    def test_deallocate_raises_errors_and_do_not_commit(
        self, batch, bus, uow, line, expected_exception
    ):
        bus.handle(commands.CreateBatch(*batch))
        
        with pytest.raises(expected_exception):
            bus.handle(commands.Deallocate(*line))
        
        assert uow.commited == False


class TestOrchestrationChangeBatchQuantity:

    def test_can_change_batch_qty(self, uow, tomorrow, bus):
        bus.handle(commands.CreateBatch('batch', 'sku', 10, tomorrow))
        bus.handle(commands.ChangeBatchQuantity('batch', 5))
        [batch] = uow.products.get(sku='sku').batches

        assert batch.available_qty == 5


    def test_change_batch_qty_reallocates_when_necessary(self, uow, tomorrow, bus):
        bus.handle(commands.CreateBatch('batch1', 'sku', 10, None))
        bus.handle(commands.CreateBatch('batch2', 'sku', 10, tomorrow))
        bus.handle(commands.Allocate('o1', 'sku', 10))
        
        product = uow.products.get_by_batch_ref('batch1')
        batch1 = next(b for b in product.batches if b.ref == 'batch1')
        assert batch1.allocated_qty == 10
        
        bus.handle(commands.ChangeBatchQuantity('batch1', 5))
        
        batch1 = next(b for b in product.batches if b.ref == 'batch1')
        batch2 = next(b for b in product.batches if b.ref == 'batch2')

        assert batch1.qty == 5
        assert batch1.available_qty == 5
        assert batch2.allocated_qty == 10
