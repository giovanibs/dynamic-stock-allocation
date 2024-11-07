from typing import List
from src.allocation.domain.model import Batch, OrderLine
from src.allocation.adapters.repository import AbstractRepository
import pytest


class FakeRepository(AbstractRepository):

    def __init__(self, batches: List[Batch]) -> None:
        self._batches = set()
        for batch in batches:
            self.add(batch)

    
    def get(self, reference: str) -> Batch:
        try:
            return next(batch for batch in self._batches if batch.reference == reference)
        except StopIteration:
            raise ValueError('Batch does not exist.')


    def add(self, batch: Batch) -> None:
        stored_batch = Batch(**batch.properties_dict)
        for line in batch.allocations:
            stored_line = OrderLine(line.order_id, line.sku, line.qty)
            stored_batch.allocate(stored_line)
        self._batches.add(stored_batch)


    def update(self, batch: Batch) -> None:
        batch_to_update = self.get(batch.reference)
        self._batches.remove(batch_to_update)
        self.add(batch)


    def list(self):
        return list(self._batches)


@pytest.fixture
def repo():
    yield FakeRepository([])


def test_can_retrieve_batch():
    batch = Batch('batch', 'sku', 100)
    repo = FakeRepository([batch])
    retrieved_batch = repo.get(batch.reference)
    assert_batches_match(retrieved_batch, batch)


def test_can_add_batch(repo):
    batch = Batch('batch', 'sku', 100)
    repo.add(batch)
    retrieved_batch = repo.get(batch.reference)
    assert_batches_match(retrieved_batch, batch)


def test_can_update_batch():
    batch = Batch('batch', 'sku', 100)
    repo = FakeRepository([batch])
    line1 = OrderLine('o1', 'sku', 10)
    batch.allocate(line1)
    repo.update(batch)
    updated_batch = repo.get(batch.reference)
    assert_batches_match(updated_batch, batch)


def test_can_list_batches():
    batches = [
        Batch('batch1', 'sku', 100),
        Batch('batch2', 'sku', 100),
        Batch('batch3', 'sku', 100),
    ]
    repo = FakeRepository(batches)
    retrieved_batches = repo.list()
    assert len(retrieved_batches) == 3

    for batch in batches:
        assert_batches_match(
            batch,
            next(b for b in retrieved_batches if b.reference == batch.reference)
        )


def assert_batches_match(batch: Batch, other_batch: Batch):
    assert batch.reference == other_batch.reference
    assert batch.sku == other_batch.sku
    assert batch.allocated_qty == other_batch.allocated_qty
    assert batch.available_qty == other_batch.available_qty
    assert batch.eta == other_batch.eta
    assert batch._allocations == other_batch._allocations
