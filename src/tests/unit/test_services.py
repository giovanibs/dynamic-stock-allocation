from typing import List

import pytest
from allocation.adapters.repository import AbstractRepository
from allocation.domain.exceptions import InvalidSKU, OutOfStock
from allocation.domain.model import Batch, OrderLine
from allocation.orchestration import services


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


class FakeSession:
    def __init__(self) -> None:
        self._commited = False

    
    @property
    def commited(self):
        return self._commited
    
    
    def commit(self):
        self._commited = True


def test_allocate_commits_on_happy_path():
    batch = Batch('batch', 'skew', 10)
    repo = FakeRepository([batch])
    line = OrderLine('o1', 'skew', 1)
    session = FakeSession()
    services.allocate(line, repo, session)
    assert session.commited == True


def test_allocate_does_not_commit_on_error():
    batch = Batch('batch', 'skew', 10)
    repo = FakeRepository([batch])
    line_with_invalid_sku = OrderLine('o1', 'invalid_skew', 1)
    line_with_greater_qty = OrderLine('o2', 'skew', 11)
    session = FakeSession()
    try:
        services.allocate(line_with_invalid_sku, repo, session)
    except InvalidSKU:
        pass
    
    assert session.commited == False

    try:
        services.allocate(line_with_greater_qty, repo, session)
    except OutOfStock:
        pass

    assert session.commited == False


def test_allocate_returns_batch_reference(today, later):
    earlier_batch = Batch('earlier', 'skew', 10, eta=today)
    later_batch = Batch('earlier', 'skew', 10, eta=later)
    repo = FakeRepository([earlier_batch, later_batch])
    line = OrderLine('o1', 'skew', 1)
    session = FakeSession()
    batch_reference = services.allocate(line, repo, session)
    assert batch_reference == earlier_batch.reference


def test_allocate_raises_error_for_invalid_sku():
    batch = Batch('batch', 'skew', 10)
    repo = FakeRepository([batch])
    line_with_invalid_sku = OrderLine('o1', 'invalid_skew', 1)
    session = FakeSession()
    with pytest.raises(InvalidSKU):
        services.allocate(line_with_invalid_sku, repo, session)


def test_allocate_raises_error_for_overallocation():
    batch = Batch('batch', 'skew', 10)
    repo = FakeRepository([batch])
    line_with_greater_qty = OrderLine('o2', 'skew', 11)
    session = FakeSession()
    with pytest.raises(OutOfStock):
        services.allocate(line_with_greater_qty, repo, session)
