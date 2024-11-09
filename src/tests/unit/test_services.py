from typing import List

import pytest
from allocation.adapters.repository import AbstractRepository
from allocation.domain.exceptions import (
    InvalidSKU, LineIsNotAllocatedError, OutOfStock, BatchDoesNotExist)
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
            raise BatchDoesNotExist('Batch does not exist.')


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
    batch = ('batch', 'skew', 10, None)
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch(*batch, repo, session)
    line = ('o1', 'skew', 1)
    
    allocate_session = FakeSession()
    services.allocate(*line, repo, allocate_session)
    assert allocate_session.commited == True


def test_allocate_does_not_commit_on_error():
    batch = ('batch', 'skew', 10, None)
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch(*batch, repo, session)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    line_with_greater_qty = ('o2', 'skew', 11)
    
    allocate_session = FakeSession()
    try:
        services.allocate(*line_with_invalid_sku, repo, allocate_session)
    except InvalidSKU:
        pass
    
    assert allocate_session.commited == False

    try:
        services.allocate(*line_with_greater_qty, repo, allocate_session)
    except OutOfStock:
        pass

    assert allocate_session.commited == False


def test_allocate_returns_batch_reference(today, later):
    earlier_batch = ('earlier', 'skew', 10, today)
    later_batch = ('earlier', 'skew', 10, later)
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch(*earlier_batch, repo, session)
    services.add_batch(*later_batch, repo, session)
    line = ('o1', 'skew', 1)
    
    allocate_session = FakeSession()
    batch_reference = services.allocate(*line, repo, allocate_session)
    assert batch_reference == earlier_batch[0]


def test_allocate_raises_error_for_invalid_sku():
    batch = ('batch', 'skew', 10, None)
    session = FakeSession()
    repo = FakeRepository([])
    services.add_batch(*batch, repo, session)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    allocate_session = FakeSession()
    with pytest.raises(InvalidSKU):
        services.allocate(*line_with_invalid_sku, repo, allocate_session)


def test_allocate_raises_error_for_overallocation():
    batch = ('batch', 'skew', 10, None)
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch(*batch, repo, session)
    line_with_greater_qty = ('o2', 'skew', 11)
    
    allocate_session = FakeSession()
    with pytest.raises(OutOfStock):
        services.allocate(*line_with_greater_qty, repo, allocate_session)


def test_deallocate_returns_batch_reference():
    batch_with_the_line = ('it_is_me', 'skew', 10, None)
    batch_without_the_line = ('it_is_not_me', 'skew', 1, None)
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch(*batch_with_the_line, repo, session)
    services.add_batch(*batch_without_the_line, repo, session)
    line = ('o1', 'skew', 10)
    services.allocate(*line, repo, session)
    
    deallocate_session = FakeSession()
    batch_reference = services.deallocate(*line, repo, deallocate_session)
    assert batch_reference == batch_with_the_line[0]


def test_deallocate_commits_on_happy_path():
    batch = ('batch', 'skew', 10, None)
    repo = FakeRepository([])
    
    session = FakeSession()
    services.add_batch(*batch, repo, session)
    line = ('o1', 'skew', 1)
    services.allocate(*line, repo, session)
    
    deallocate_session = FakeSession()
    services.deallocate(*line, repo, deallocate_session)
    assert deallocate_session.commited == True


def test_deallocate_does_not_commit_on_error():
    batch = ('batch', 'skew', 10, None)
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch(*batch, repo, session)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    line_not_allocated = ('o2', 'skew', 1)
    
    deallocate_session = FakeSession()
    try:
        services.deallocate(*line_with_invalid_sku, repo, deallocate_session)
    except InvalidSKU:
        pass
    
    assert deallocate_session.commited == False

    try:
        services.deallocate(*line_not_allocated, repo, deallocate_session)
    except LineIsNotAllocatedError:
        pass

    assert deallocate_session.commited == False


def test_deallocate_raises_error_for_invalid_sku():
    batch = ('batch', 'skew', 10, None)
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch(*batch, repo, session)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    deallocate_session = FakeSession()
    with pytest.raises(InvalidSKU):
        services.deallocate(*line_with_invalid_sku, repo, deallocate_session)


def test_deallocate_raises_error_for_not_allocated_line():
    batch = ('batch', 'skew', 10, None)
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch(*batch, repo, session)
    line_not_allocated = ('o2', 'skew', 1)
    
    deallocate_session = FakeSession()
    with pytest.raises(LineIsNotAllocatedError):
        services.deallocate(*line_not_allocated, repo, deallocate_session)


def test_add_batch():
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch('batch', 'skew', 10, None, repo, session)
    assert repo.get('batch').reference == 'batch'


def test_add_batch_commits_on_happy_path():
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch('batch', 'skew', 10, None, repo, session)
    assert session.commited
