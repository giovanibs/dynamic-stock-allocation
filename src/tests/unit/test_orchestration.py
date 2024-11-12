from typing import List, Optional
import pytest
from allocation.adapters.repository import AbstractRepository
from allocation.domain import events
from allocation.domain.exceptions import (
    InexistentProduct, LineIsNotAllocatedError, OutOfStock)
from allocation.orchestration import services
from allocation.domain.model import Product
from allocation.orchestration.uow import AbstractUnitOfWork
from dddjango.alloc.models import Product
from allocation.orchestration import message_bus


class FakeProductRepository(AbstractRepository):

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


class FakeProductUoW(AbstractUnitOfWork):

        def __init__(self, repo: AbstractRepository) -> None:
            self._products = repo
            self._commited = False
            self.collected_events = set()


        @property
        def commited(self) -> bool:
            return self._commited
        

        @property
        def products(self) -> AbstractRepository:
            return self._products
        

        def __enter__(self) -> AbstractUnitOfWork:
            self._commited = False
            return super().__enter__()
        

        def __exit__(self, *args) -> None:
            return super().__exit__(*args)


        def _commit(self):
            self.collected_events.update(list(self.collect_new_events()))
            if events.OutOfStock in {type(event) for event in self.collected_events}:
                return
            self._commited = True


        def rollback(self):
            pass


@pytest.fixture
def uow():
    return FakeProductUoW(FakeProductRepository())


@pytest.fixture
def batch(tomorrow):
    return ('batch', 'skew', 10, tomorrow)


class TestServicesAdd:

    def test_can_add_a_batch(self, batch, uow):
        message_bus.handle(events.BatchCreated(*batch), uow)
        product = uow.products.get(batch[1])
        assert batch[0] in {b.ref for b in product.batches}
        assert uow.commited


    def test_adding_a_batch_also_adds_a_new_product(self, batch, uow):
        with pytest.raises(InexistentProduct):
            uow.products.get(batch[1])

        message_bus.handle(events.BatchCreated(*batch), uow)
        product = uow.products.get(batch[1])
        assert batch[0] in {b.ref for b in product.batches}


class TestServicesAllocate:

    def test_allocate_commits_on_happy_path(self, batch, uow):
        message_bus.handle(events.BatchCreated(*batch), uow)
        line = ('o1', 'skew', 1)
        
        services.allocate(*line, uow)
        assert uow.commited == True


    def test_allocate_does_not_commit_on_error(self, batch, uow):
        message_bus.handle(events.BatchCreated(*batch), uow)
        line_with_invalid_sku = ('o1', 'invalid_skew', 1)
        line_with_greater_qty = ('o2', 'skew', 11)
        
        try:
            services.allocate(*line_with_invalid_sku, uow)
        except InexistentProduct:
            pass
        
        assert uow.commited == False

        ref = services.allocate(*line_with_greater_qty, uow)
        assert ref == None
        assert uow.commited == False


    def test_allocate_returns_batch_ref(self, today, later, uow):
        earlier_batch = ('earlier', 'skew', 10, today)
        later_batch = ('earlier', 'skew', 10, later)
        message_bus.handle(events.BatchCreated(*earlier_batch), uow)
        message_bus.handle(events.BatchCreated(*later_batch), uow)
        line = ('o1', 'skew', 1)
        
        batch_ref = services.allocate(*line, uow)
        assert batch_ref == earlier_batch[0]


    def test_allocate_raises_error_for_invalid_sku(self, batch, uow):
        message_bus.handle(events.BatchCreated(*batch), uow)
        line_with_invalid_sku = ('o1', 'invalid_skew', 1)
        
        with pytest.raises(InexistentProduct):
            services.allocate(*line_with_invalid_sku, uow)


    def test_allocate_raises_event_for_overallocation(self, batch, uow):
        message_bus.handle(events.BatchCreated(*batch), uow)
        line_with_greater_qty = ('o2', 'skew', 11)
        services.allocate(*line_with_greater_qty, uow)
        
        assert events.OutOfStock in {type(event) for event in uow.collected_events}


class TestServicesDeallocate:

    def test_deallocate_returns_batch_ref(self, uow):
        batch_with_the_line = ('it_is_me', 'skew', 10, None)
        batch_without_the_line = ('it_is_not_me', 'skew', 1, None)
        message_bus.handle(events.BatchCreated(*batch_with_the_line), uow)
        message_bus.handle(events.BatchCreated(*batch_without_the_line), uow)
        line = ('o1', 'skew', 10)
        services.allocate(*line, uow)
        
        batch_ref = services.deallocate(*line, uow)
        assert batch_ref == batch_with_the_line[0]


    def test_deallocate_commits_on_happy_path(self, batch, uow):
        message_bus.handle(events.BatchCreated(*batch), uow)
        line = ('o1', 'skew', 1)
        services.allocate(*line, uow)
        
        services.deallocate(*line, uow)
        assert uow.commited == True


    def test_deallocate_does_not_commit_on_error(self, batch, uow):
        message_bus.handle(events.BatchCreated(*batch), uow)
        line_with_invalid_sku = ('o1', 'invalid_skew', 1)
        line_not_allocated = ('o2', 'skew', 1)
        
        try:
            services.deallocate(*line_with_invalid_sku, uow)
        except InexistentProduct:
            pass
        
        assert uow.commited == False

        try:
            services.deallocate(*line_not_allocated, uow)
        except LineIsNotAllocatedError:
            pass

        assert uow.commited == False


    def test_deallocate_raises_error_for_invalid_sku(self, batch, uow):
        message_bus.handle(events.BatchCreated(*batch), uow)
        line_with_invalid_sku = ('o1', 'invalid_skew', 1)
        
        with pytest.raises(InexistentProduct):
            services.deallocate(*line_with_invalid_sku, uow)


    def test_deallocate_raises_error_for_not_allocated_line(self, batch, uow):
        message_bus.handle(events.BatchCreated(*batch), uow)
        line_not_allocated = ('o2', 'skew', 1)
        
        with pytest.raises(LineIsNotAllocatedError):
            services.deallocate(*line_not_allocated, uow)
