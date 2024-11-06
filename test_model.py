from datetime import date, timedelta
from model import Batch, OrderLine, allocate
from exceptions import CannotOverallocateError, LineIsNotAllocatedError, SKUsDontMatchError
import pytest


@pytest.fixture
def today():
    return date.today()


@pytest.fixture
def tomorrow(today):
    return today + timedelta(days=1)


@pytest.fixture
def later(today):
    return today + timedelta(days=2)


def create_batch_and_order_line(batch_qty, order_line_qty):
    dummy_sku = 'product_000'
    
    return (
        Batch('batch_000', dummy_sku, batch_qty, date.today()),
        OrderLine('order_000', dummy_sku, order_line_qty)
    )


def test_allocating_reduces_available_quantity():
    initial_available_qty = 10
    order_qty = 5
    
    batch, order_line = create_batch_and_order_line(
        initial_available_qty, order_qty
    )
    batch.allocate(order_line)
    assert batch.available_qty == (initial_available_qty - order_qty)


def test_cannot_overallocate():
    batch, order_line = create_batch_and_order_line(10, 15)

    with pytest.raises(CannotOverallocateError):
        batch.allocate(order_line)


def test_can_allocate_if_available_greater_than_required():
    batch, order_line = create_batch_and_order_line(10, 5)
    batch.allocate(order_line)


def test_can_allocate_if_available_equal_to_required():
    batch, order_line = create_batch_and_order_line(10, 10)
    batch.allocate(order_line)


def test_cannot_allocate_if_skus_dont_match():
    batch = Batch('batch_000', 'sku_000', 10, date.today())
    order_line = OrderLine('order_000', 'sku_001', 5)

    with pytest.raises(SKUsDontMatchError):
        batch.allocate(order_line)


def test_can_deallocate_allocated_order_line():
    batch, order_line = create_batch_and_order_line(10, 5)
    batch.allocate(order_line)
    batch.deallocate(order_line)
    assert order_line not in batch._allocations
    assert batch.available_qty == 10


def test_cannot_deallocate_unallocated_line():
    batch, order_line = create_batch_and_order_line(10, 5)
    
    with pytest.raises(LineIsNotAllocatedError):
        batch.deallocate(order_line)


def test_allocation_is_idempotent():
    batch, order_line = create_batch_and_order_line(10, 5)
    batch.allocate(order_line)
    batch.allocate(order_line)
    assert batch.allocated_qty == order_line.qty


def test_prefers_current_stock_batches_to_shipments(tomorrow):
    sku = 'skew'
    
    in_stock_batch = Batch('in-stock', sku, 10, eta=None)
    shipping_batch = Batch('shipping', sku, 10, eta=tomorrow)
    line = OrderLine('order_ref', sku, 5)
    
    allocate(line, [in_stock_batch, shipping_batch])

    assert in_stock_batch.available_qty == 5
    assert shipping_batch.available_qty == 10


def test_prefers_earlier_batches(today, tomorrow, later):
    sku = 'skew'
    earliest_batch = Batch('today', sku, 10, eta=today)
    in_between_batch = Batch('tomorrow', sku, 10, eta=tomorrow)
    latest_batch = Batch('latest', sku, 10, eta=later)
    line = OrderLine('order_ref', sku, 5)

    allocate(line, [earliest_batch, in_between_batch, latest_batch])

    assert earliest_batch.available_qty == 5
    assert in_between_batch.available_qty == 10
    assert latest_batch.available_qty == 10
