import pytest
from allocation.domain.exceptions import (
    BatchDoesNotExist, InvalidSKU, LineIsNotAllocatedError, OutOfStock)
from allocation.orchestration import services


@pytest.fixture
def batch(tomorrow):
    return ('batch', 'skew', 10, tomorrow)


def test_allocate_commits_on_happy_path(batch, fake_uow, fake_session):
    services.add_batch(*batch, fake_uow)
    line = ('o1', 'skew', 1)
    
    session = fake_session()
    services.allocate(*line, fake_uow.batches, session)
    assert session.commited == True


def test_allocate_does_not_commit_on_error(batch, fake_uow, fake_session):
    services.add_batch(*batch, fake_uow)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    line_with_greater_qty = ('o2', 'skew', 11)
    
    session = fake_session()
    try:
        services.allocate(*line_with_invalid_sku, fake_uow.batches, session)
    except InvalidSKU:
        pass
    
    assert session.commited == False

    try:
        services.allocate(*line_with_greater_qty, fake_uow.batches, session)
    except OutOfStock:
        pass

    assert session.commited == False


def test_allocate_returns_batch_reference(today, later, fake_uow, fake_session):
    earlier_batch = ('earlier', 'skew', 10, today)
    later_batch = ('earlier', 'skew', 10, later)
    services.add_batch(*earlier_batch, fake_uow)
    services.add_batch(*later_batch, fake_uow)
    line = ('o1', 'skew', 1)
    
    session = fake_session()
    batch_reference = services.allocate(*line, fake_uow.batches, session)
    assert batch_reference == earlier_batch[0]


def test_allocate_raises_error_for_invalid_sku(batch, fake_uow, fake_session):
    services.add_batch(*batch, fake_uow)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    session = fake_session()
    with pytest.raises(InvalidSKU):
        services.allocate(*line_with_invalid_sku, fake_uow.batches, session)


def test_allocate_raises_error_for_overallocation(batch, fake_uow, fake_session):
    services.add_batch(*batch, fake_uow)
    line_with_greater_qty = ('o2', 'skew', 11)
    
    session = fake_session()
    with pytest.raises(OutOfStock):
        services.allocate(*line_with_greater_qty, fake_uow.batches, session)


def test_deallocate_returns_batch_reference(fake_uow, fake_session):
    batch_with_the_line = ('it_is_me', 'skew', 10, None)
    batch_without_the_line = ('it_is_not_me', 'skew', 1, None)
    services.add_batch(*batch_with_the_line, fake_uow)
    services.add_batch(*batch_without_the_line, fake_uow)
    line = ('o1', 'skew', 10)
    services.allocate(*line, fake_uow.batches, fake_session())
    
    session = fake_session()
    batch_reference = services.deallocate(*line, fake_uow.batches, session)
    assert batch_reference == batch_with_the_line[0]


def test_deallocate_commits_on_happy_path(batch, fake_uow, fake_session):
    services.add_batch(*batch, fake_uow)
    line = ('o1', 'skew', 1)
    services.allocate(*line, fake_uow.batches, fake_session())
    
    session = fake_session()
    services.deallocate(*line, fake_uow.batches, session)
    assert session.commited == True


def test_deallocate_does_not_commit_on_error(batch, fake_uow, fake_session):
    services.add_batch(*batch, fake_uow)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    line_not_allocated = ('o2', 'skew', 1)
    
    session = fake_session()
    try:
        services.deallocate(*line_with_invalid_sku, fake_uow.batches, session)
    except InvalidSKU:
        pass
    
    assert session.commited == False

    try:
        services.deallocate(*line_not_allocated, fake_uow.batches, session)
    except LineIsNotAllocatedError:
        pass

    assert session.commited == False


def test_deallocate_raises_error_for_invalid_sku(batch, fake_uow, fake_session):
    services.add_batch(*batch, fake_uow)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    session = fake_session()
    with pytest.raises(InvalidSKU):
        services.deallocate(*line_with_invalid_sku, fake_uow.batches, session)


def test_deallocate_raises_error_for_not_allocated_line(batch, fake_uow, fake_session):
    services.add_batch(*batch, fake_uow)
    line_not_allocated = ('o2', 'skew', 1)
    
    session = fake_session()
    with pytest.raises(LineIsNotAllocatedError):
        services.deallocate(*line_not_allocated, fake_uow.batches, session)


def test_add_batch(batch, fake_uow):
    services.add_batch(*batch, fake_uow)
    assert fake_uow.batches.get('batch').reference == batch[0]


def test_add_batch_commits_on_happy_path(batch, fake_uow):
    services.add_batch(*batch, fake_uow)
    assert fake_uow.commited
