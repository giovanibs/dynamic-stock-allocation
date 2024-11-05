from datetime import date
from model import Batch, OrderLine
from exceptions import CannotOverallocateError, SKUsDontMatchError
import pytest


def create_batch_and_order_line(batch_qty, order_line_qty):
    dummy_sku = 'product_000'
    
    return (
        Batch('batch_000', dummy_sku, batch_qty, date.today()),
        OrderLine('order_line_000', dummy_sku, order_line_qty)
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
    order_line = OrderLine('order_line_000', 'sku_001', 5)

    with pytest.raises(SKUsDontMatchError):
        batch.allocate(order_line)
