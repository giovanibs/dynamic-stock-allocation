from typing import List, Optional
from allocation.domain.model import Batch, OrderLine, Product
from allocation.adapters.repository import AbstractRepository
from allocation.domain.exceptions import BatchDoesNotExist, InexistentProduct


class FakeProductRepository(AbstractRepository):

        def __init__(self, products: Optional[List[Product]] = None) -> None:
            super().__init__()
            self._products = set(products) if products is not None else set()


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


def test_can_retrieve_product():
    product = Product('sku')
    repo = FakeProductRepository([product])
    retrieved_product = repo.get('sku')
    assert product.sku == retrieved_product.sku


def test_can_add_product():
    product = Product('sku')
    repo = FakeProductRepository()
    repo.add(product)
    retrieved_product = repo.get(product.sku)
    assert product.sku == retrieved_product.sku


def test_can_update_product():
    product = Product('sku')
    repo = FakeProductRepository([product])
    batch = Batch('batch', 'sku', 100)
    updated_product = Product('sku', [batch])
    repo.update(updated_product)
    retrieved_product = repo.get(product.sku)
    assert updated_product.sku == retrieved_product.sku
    assert updated_product.batches == retrieved_product.batches


def test_can_list_product():
    products = [
        Product('sku'),
        Product('sku2'),
    ]
    repo = FakeProductRepository(products)
    retrieved_products = repo.list()
    assert len(retrieved_products) == 2

    for product in products:
        assert product.sku in {p.sku for p in retrieved_products}
