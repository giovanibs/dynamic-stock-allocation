from datetime import date
from model import Batch, OrderLine


class TestBatchAllocation:

    def test_allocating_reduces_available_quantity(self):
        dummy_sku = 'product_000'
        initial_available_qty = 10
        order_qty = 5
        
        batch = Batch(
            ref = 'batch_000',
            sku = dummy_sku,
            available_qty = initial_available_qty,
            eta = date.today()
        )

        order_line = OrderLine(
            ref = 'order_line_000',
            sku = dummy_sku,
            qty = order_qty 
        )

        batch.allocate(order_line)

        assert batch.available_qty == (initial_available_qty - order_qty)
