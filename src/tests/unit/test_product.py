from allocation.domain import events
from allocation.domain.model import Batch, OrderLine, Product
from allocation.domain.exceptions import InvalidSKU, LineIsNotAllocatedError
import pytest


def test_prefers_current_stock_batches_to_shipments(tomorrow):
    sku = 'skew'
    in_stock_batch = Batch('in-stock', sku, 10, eta=None)
    shipping_batch = Batch('shipping', sku, 10, eta=tomorrow)
    product = Product(sku, [in_stock_batch, shipping_batch])
    line = ('order_ref', sku, 5)
    product.allocate(*line)

    assert in_stock_batch.available_qty == 5
    assert shipping_batch.available_qty == 10


def test_prefers_earlier_batches(today, tomorrow, later):
    sku = 'skew'
    earliest_batch = Batch('today', sku, 10, eta=today)
    in_between_batch = Batch('tomorrow', sku, 10, eta=tomorrow)
    latest_batch = Batch('latest', sku, 10, eta=later)
    line = ('order_ref', sku, 5)
    product = Product(sku, [earliest_batch, in_between_batch, latest_batch])
    product.allocate(*line)

    assert earliest_batch.available_qty == 5
    assert in_between_batch.available_qty == 10
    assert latest_batch.available_qty == 10


def test_allocation_returns_allocated_batch_ref(today, tomorrow, later):
    sku = 'skew'
    earliest_batch = Batch('today', sku, 10, eta=today)
    in_between_batch = Batch('tomorrow', sku, 10, eta=tomorrow)
    latest_batch = Batch('latest', sku, 10, eta=later)
    line = ('order_ref', sku, 5)
    product = Product(sku, [earliest_batch, in_between_batch, latest_batch])
    batch_ref = product.allocate(*line)

    assert batch_ref == earliest_batch.ref


def test_deallocate_returns_batch_ref():
    sku = 'skew'
    batch_with_the_line = Batch('it_is_me', sku, 10)
    batch_without_the_line = Batch('it_is_not_me', sku, 10)
    line = ('o1', sku, 1)
    batch_with_the_line.allocate(OrderLine(*line))
    product = Product(sku, [batch_with_the_line, batch_without_the_line])
    batch_ref = product.deallocate(*line)

    assert batch_ref == batch_with_the_line.ref


def test_deallocate_raises_error_for_invalid_sku():
    batch = Batch('batch', 'skew', 10)
    other_batch = Batch('other_batch', 'skew', 10)
    product = Product('skew', [batch, other_batch])
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    with pytest.raises(InvalidSKU):
        product.deallocate(*line_with_invalid_sku)


def test_deallocate_raises_error_for_not_allocated_line():
    batch_without_the_line = Batch('it_is_not_me', 'skew', 10)
    other_batch_without_the_line = Batch('it_is_not_me_either', 'skew', 10)
    product = Product('skew', [batch_without_the_line, other_batch_without_the_line])
    line_not_allocated = ('o1', 'skew', 1)
    
    with pytest.raises(LineIsNotAllocatedError):
        product.deallocate(*line_not_allocated)


def test_can_add_valid_batch():
    product = Product('sku')
    batch = ('batch', 'sku', 10)
    product.add_batch(*batch)
    assert 'batch' in {b.ref for b in product.batches}


def test_cannot_add_batch_with_different_sku():
    product = Product('sku')
    batch = ('batch', 'other_sku', 10)
    
    with pytest.raises(InvalidSKU):
        product.add_batch(*batch)


def test_can_instantiate_product_with_batches():
    batch = Batch('batch', 'skew', 10)
    other_batch = Batch('other_batch', 'skew', 10)
    product = Product('skew', [batch, other_batch])
    assert batch.ref in {b.ref for b in product.batches}
    assert other_batch.ref in {b.ref for b in product.batches}


def test_cannot_instantiate_product_with_invalid_batch():
    batch = Batch('batch', 'other_skew', 10)
    
    with pytest.raises(InvalidSKU):
        Product('skew', [batch])


def test_records_out_of_stock_event_if_cannot_allocate():
    sku = 'skew'
    product = Product(sku)
    product.add_batch('batch', sku, 1)
    allocation = product.allocate('o1', sku, 2)

    assert product.messages[0] == events.OutOfStock(sku)
    assert allocation is None
