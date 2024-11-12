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
            self.events = []


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
            self._commited = True


        def rollback(self):
            pass


        def event_handler(self, event: events.Event):
            self.events.append(event)


@pytest.fixture
def uow():
    return FakeProductUoW(FakeProductRepository())


@pytest.fixture
def batch(tomorrow):
    return ('batch', 'skew', 10, tomorrow)


class TestServicesAdd:

    def test_can_add_a_batch(self, batch, uow):
        services.add_batch(*batch, uow)
        product = uow.products.get(batch[1])
        assert batch[0] in {b.ref for b in product.batches}


    def test_adding_a_batch_also_adds_a_new_product(self, batch, uow):
        with pytest.raises(InexistentProduct):
            uow.products.get(batch[1])

        services.add_batch(*batch, uow)
        product = uow.products.get(batch[1])
        assert batch[0] in {b.ref for b in product.batches}


class TestServicesAllocate:

    def test_allocate_commits_on_happy_path(self, batch, uow):
        services.add_batch(*batch, uow)
        line = ('o1', 'skew', 1)
        
        services.allocate(*line, uow)
        assert uow.commited == True


    @pytest.mark.skip
    def test_allocate_does_not_commit_on_error(self, batch, uow):
        services.add_batch(*batch, uow)
        line_with_invalid_sku = ('o1', 'invalid_skew', 1)
        line_with_greater_qty = ('o2', 'skew', 11)
        
        try:
            services.allocate(*line_with_invalid_sku, uow)
        except InexistentProduct:
            pass
        
        assert uow.commited == False

        try:
            services.allocate(*line_with_greater_qty, uow)
        except OutOfStock:
            pass

        assert uow.commited == False


    def test_allocate_returns_batch_ref(self, today, later, uow):
        earlier_batch = ('earlier', 'skew', 10, today)
        later_batch = ('earlier', 'skew', 10, later)
        services.add_batch(*earlier_batch, uow)
        services.add_batch(*later_batch, uow)
        line = ('o1', 'skew', 1)
        
        batch_ref = services.allocate(*line, uow)
        assert batch_ref == earlier_batch[0]


    def test_allocate_raises_error_for_invalid_sku(self, batch, uow):
        services.add_batch(*batch, uow)
        line_with_invalid_sku = ('o1', 'invalid_skew', 1)
        
        with pytest.raises(InexistentProduct):
            services.allocate(*line_with_invalid_sku, uow)


    @pytest.mark.skip
    def test_allocate_raises_error_for_overallocation(self, batch, uow):
        services.add_batch(*batch, uow)
        line_with_greater_qty = ('o2', 'skew', 11)
        
        with pytest.raises(OutOfStock):
            services.allocate(*line_with_greater_qty, uow)


class TestServicesDeallocate:

    def test_deallocate_returns_batch_ref(self, uow):
        batch_with_the_line = ('it_is_me', 'skew', 10, None)
        batch_without_the_line = ('it_is_not_me', 'skew', 1, None)
        services.add_batch(*batch_with_the_line, uow)
        services.add_batch(*batch_without_the_line, uow)
        line = ('o1', 'skew', 10)
        services.allocate(*line, uow)
        
        batch_ref = services.deallocate(*line, uow)
        assert batch_ref == batch_with_the_line[0]


    def test_deallocate_commits_on_happy_path(self, batch, uow):
        services.add_batch(*batch, uow)
        line = ('o1', 'skew', 1)
        services.allocate(*line, uow)
        
        services.deallocate(*line, uow)
        assert uow.commited == True


    def test_deallocate_does_not_commit_on_error(self, batch, uow):
        services.add_batch(*batch, uow)
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
        services.add_batch(*batch, uow)
        line_with_invalid_sku = ('o1', 'invalid_skew', 1)
        
        with pytest.raises(InexistentProduct):
            services.deallocate(*line_with_invalid_sku, uow)


    def test_deallocate_raises_error_for_not_allocated_line(self, batch, uow):
        services.add_batch(*batch, uow)
        line_not_allocated = ('o2', 'skew', 1)
        
        with pytest.raises(LineIsNotAllocatedError):
            services.deallocate(*line_not_allocated, uow)


class TestEvents:

    def test_uow_can_collect_events_and_pass_to_handler(self, batch, uow):
        services.add_batch(*batch, uow)
        line_with_greater_qty = ('o2', 'skew', 11)

        try:
            services.allocate(*line_with_greater_qty, uow)
        except OutOfStock:
            pass

        assert uow.events[0] == events.OutOfStock('skew')

