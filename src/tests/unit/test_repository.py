from typing import List
from src.allocation.domain.model import Batch
from src.allocation.adapters.repository import AbstractRepository
import pytest


class FakeRepository(AbstractRepository):

    def __init__(self, batches: List[Batch]) -> None:
        self._batches = set(batches)

    
    def get(self, reference: str) -> Batch:
        try:
            return next(batch for batch in self._batches if batch.reference == reference)
        except StopIteration:
            raise ValueError('Batch does not exist.')


    def add(self, batch: Batch) -> None:
        self._batches.add(batch)


    def update(self, batch: Batch) -> None:
        return super().update(batch)


@pytest.fixture
def repo():
    return FakeRepository([])


def test_can_add_batch(repo):
    batch = Batch('batch', 'sku', 100, eta=None)
    repo.add(batch)
    
    retrieved_batch = repo.get(batch.reference)

    assert retrieved_batch == batch
