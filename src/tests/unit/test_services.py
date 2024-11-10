from typing import List, Optional
import pytest
from allocation.adapters.repository import AbstractProductRepository
from allocation.domain.exceptions import (
    InexistentProduct, InvalidSKU, LineIsNotAllocatedError, OutOfStock)
from allocation.orchestration import services
from allocation.domain.model import Product
from allocation.orchestration.uow import AbstractProductUnitOfWork, AbstractUnitOfWork


class FakeProductRepository(AbstractProductRepository):

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


class FakeProductUoW(AbstractProductUnitOfWork):

        def __init__(self, repo: AbstractProductRepository) -> None:
            self._products = repo
            self._commited = False


        @property
        def commited(self) -> bool:
            return self._commited
        

        @property
        def products(self) -> AbstractProductRepository:
            return self._products
        

        def __enter__(self) -> AbstractUnitOfWork:
            self._commited = False
            return super().__enter__()
        

        def __exit__(self, *args) -> None:
            return super().__exit__(*args)


        def commit(self):
            self._commited = True


        def rollback(self):
            pass


@pytest.fixture
def uow():
    return FakeProductUoW(FakeProductRepository())


@pytest.fixture
def batch(tomorrow):
    return ('batch', 'skew', 10, tomorrow)


class TestAddBatch:

    def test_add_batch(self, batch, uow):
        services.add_batch(*batch, uow)
        product = uow.products.get(batch[1])
        assert batch[0] in {b.reference for b in product.batches}


    def test_add_batch_commits_on_happy_path(self, batch, uow):
        services.add_batch(*batch, uow)
        assert uow.commited


class TestAllocate:

    def test_allocate_commits_on_happy_path(self, batch, uow):
        services.add_batch(*batch, uow)
        line = ('o1', 'skew', 1)
        
        services.allocate(*line, uow)
        assert uow.commited == True


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


    def test_allocate_returns_batch_reference(self, today, later, uow):
        earlier_batch = ('earlier', 'skew', 10, today)
        later_batch = ('earlier', 'skew', 10, later)
        services.add_batch(*earlier_batch, uow)
        services.add_batch(*later_batch, uow)
        line = ('o1', 'skew', 1)
        
        batch_reference = services.allocate(*line, uow)
        assert batch_reference == earlier_batch[0]


    def test_allocate_raises_error_for_invalid_sku(self, batch, uow):
        services.add_batch(*batch, uow)
        line_with_invalid_sku = ('o1', 'invalid_skew', 1)
        
        with pytest.raises(InexistentProduct):
            services.allocate(*line_with_invalid_sku, uow)


    def test_allocate_raises_error_for_overallocation(self, batch, uow):
        services.add_batch(*batch, uow)
        line_with_greater_qty = ('o2', 'skew', 11)
        
        with pytest.raises(OutOfStock):
            services.allocate(*line_with_greater_qty, uow)


@pytest.mark.skip('One refactor at a time!')
def test_deallocate_returns_batch_reference(uow):
    batch_with_the_line = ('it_is_me', 'skew', 10, None)
    batch_without_the_line = ('it_is_not_me', 'skew', 1, None)
    services.add_batch(*batch_with_the_line, uow)
    services.add_batch(*batch_without_the_line, uow)
    line = ('o1', 'skew', 10)
    services.allocate(*line, uow)
    
    batch_reference = services.deallocate(*line, uow)
    assert batch_reference == batch_with_the_line[0]


@pytest.mark.skip('One refactor at a time!')
def test_deallocate_commits_on_happy_path(batch, uow):
    services.add_batch(*batch, uow)
    line = ('o1', 'skew', 1)
    services.allocate(*line, uow)
    
    services.deallocate(*line, uow)
    assert uow.commited == True


@pytest.mark.skip('One refactor at a time!')
def test_deallocate_does_not_commit_on_error(batch, uow):
    services.add_batch(*batch, uow)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    line_not_allocated = ('o2', 'skew', 1)
    
    try:
        services.deallocate(*line_with_invalid_sku, uow)
    except InvalidSKU:
        pass
    
    assert uow.commited == False

    try:
        services.deallocate(*line_not_allocated, uow)
    except LineIsNotAllocatedError:
        pass

    assert uow.commited == False


@pytest.mark.skip('One refactor at a time!')
def test_deallocate_raises_error_for_invalid_sku(batch, uow):
    services.add_batch(*batch, uow)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    with pytest.raises(InvalidSKU):
        services.deallocate(*line_with_invalid_sku, uow)


@pytest.mark.skip('One refactor at a time!')
def test_deallocate_raises_error_for_not_allocated_line(batch, uow):
    services.add_batch(*batch, uow)
    line_not_allocated = ('o2', 'skew', 1)
    
    with pytest.raises(LineIsNotAllocatedError):
        services.deallocate(*line_not_allocated, uow)
