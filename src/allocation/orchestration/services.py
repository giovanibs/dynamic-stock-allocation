"""
Typical service-layer functions have similar steps:

(1) We fetch some objects from the repository.
(2) We make some checks or assertions about the request against the current state of the world.
(3) We call a domain service.
(4) If all is well, we save/update any state we’ve changed.
"""
from typing import List
from allocation.adapters.repository import AbstractRepository
from allocation.domain import model as domain_models
from allocation.domain.exceptions import InvalidSKU, LineIsNotAllocatedError


def allocate(line: domain_models.OrderLine, repo: AbstractRepository, session):
    batches = repo.list()                                       # (1)
    
    if line.sku not in {batch.sku for batch in batches}:        # (2)
        raise InvalidSKU()
    
    batch_reference = domain_models.allocate(line, batches)     # (3)
    repo.update(next(b for b in batches if b.reference == batch_reference))
    session.commit()                                            # (4)
    return batch_reference


def deallocate(line: domain_models.OrderLine, repo: AbstractRepository, session):
    batches = repo.list()
    
    if line.sku not in {batch.sku for batch in batches}:
        raise InvalidSKU()
    
    batch = _find_batch_with_allocated_line(line, batches)
    
    if not batch:
        raise LineIsNotAllocatedError()
    
    batch.deallocate(line)
    repo.update(batch)
    session.commit()
    return batch.reference


def _find_batch_with_allocated_line(line, batches: List[domain_models.Batch]):
    try:
        return next(batch for batch in batches if line in batch.allocations)
    except StopIteration:
        return None
