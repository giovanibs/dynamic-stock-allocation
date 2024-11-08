"""
Typical service-layer functions have similar steps:

(1) We fetch some objects from the repository.
(2) We make some checks or assertions about the request against the current state of the world.
(3) We call a domain service.
(4) If all is well, we save/update any state we’ve changed.
"""
from allocation.adapters.repository import AbstractRepository
from allocation.domain import model as domain_models
from allocation.domain.exceptions import InvalidSKU


def allocate(line: domain_models.OrderLine, repo: AbstractRepository, session):
    batches = repo.list()                                       # (1)
    
    if line.sku not in {batch.sku for batch in batches}:        # (2)
        raise InvalidSKU()
    
    batch_reference = domain_models.allocate(line, batches)     # (3)
    session.commit()                                            # (4)
    return batch_reference
