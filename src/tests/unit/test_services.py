import pytest
from allocation.domain.exceptions import (
    InvalidSKU, LineIsNotAllocatedError, OutOfStock)
from allocation.orchestration import services


def test_allocate_commits_on_happy_path(fake_repository, fake_session):
    batch = ('batch', 'skew', 10, None)
    repo = fake_repository([])
    session = fake_session()
    services.add_batch(*batch, repo, session)
    line = ('o1', 'skew', 1)
    
    allocate_session = fake_session()
    services.allocate(*line, repo, allocate_session)
    assert allocate_session.commited == True


def test_allocate_does_not_commit_on_error(fake_repository, fake_session):
    batch = ('batch', 'skew', 10, None)
    repo = fake_repository([])
    session = fake_session()
    services.add_batch(*batch, repo, session)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    line_with_greater_qty = ('o2', 'skew', 11)
    
    allocate_session = fake_session()
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


def test_allocate_returns_batch_reference(today, later, fake_repository, fake_session):
    earlier_batch = ('earlier', 'skew', 10, today)
    later_batch = ('earlier', 'skew', 10, later)
    repo = fake_repository([])
    session = fake_session()
    services.add_batch(*earlier_batch, repo, session)
    services.add_batch(*later_batch, repo, session)
    line = ('o1', 'skew', 1)
    
    allocate_session = fake_session()
    batch_reference = services.allocate(*line, repo, allocate_session)
    assert batch_reference == earlier_batch[0]


def test_allocate_raises_error_for_invalid_sku(fake_repository, fake_session):
    batch = ('batch', 'skew', 10, None)
    session = fake_session()
    repo = fake_repository([])
    services.add_batch(*batch, repo, session)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    allocate_session = fake_session()
    with pytest.raises(InvalidSKU):
        services.allocate(*line_with_invalid_sku, repo, allocate_session)


def test_allocate_raises_error_for_overallocation(fake_repository, fake_session):
    batch = ('batch', 'skew', 10, None)
    repo = fake_repository([])
    session = fake_session()
    services.add_batch(*batch, repo, session)
    line_with_greater_qty = ('o2', 'skew', 11)
    
    allocate_session = fake_session()
    with pytest.raises(OutOfStock):
        services.allocate(*line_with_greater_qty, repo, allocate_session)


def test_deallocate_returns_batch_reference(fake_repository, fake_session):
    batch_with_the_line = ('it_is_me', 'skew', 10, None)
    batch_without_the_line = ('it_is_not_me', 'skew', 1, None)
    repo = fake_repository([])
    session = fake_session()
    services.add_batch(*batch_with_the_line, repo, session)
    services.add_batch(*batch_without_the_line, repo, session)
    line = ('o1', 'skew', 10)
    services.allocate(*line, repo, session)
    
    deallocate_session = fake_session()
    batch_reference = services.deallocate(*line, repo, deallocate_session)
    assert batch_reference == batch_with_the_line[0]


def test_deallocate_commits_on_happy_path(fake_repository, fake_session):
    batch = ('batch', 'skew', 10, None)
    repo = fake_repository([])
    
    session = fake_session()
    services.add_batch(*batch, repo, session)
    line = ('o1', 'skew', 1)
    services.allocate(*line, repo, session)
    
    deallocate_session = fake_session()
    services.deallocate(*line, repo, deallocate_session)
    assert deallocate_session.commited == True


def test_deallocate_does_not_commit_on_error(fake_repository, fake_session):
    batch = ('batch', 'skew', 10, None)
    repo = fake_repository([])
    session = fake_session()
    services.add_batch(*batch, repo, session)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    line_not_allocated = ('o2', 'skew', 1)
    
    deallocate_session = fake_session()
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


def test_deallocate_raises_error_for_invalid_sku(fake_repository, fake_session):
    batch = ('batch', 'skew', 10, None)
    repo = fake_repository([])
    session = fake_session()
    services.add_batch(*batch, repo, session)
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    deallocate_session = fake_session()
    with pytest.raises(InvalidSKU):
        services.deallocate(*line_with_invalid_sku, repo, deallocate_session)


def test_deallocate_raises_error_for_not_allocated_line(fake_repository, fake_session):
    batch = ('batch', 'skew', 10, None)
    repo = fake_repository([])
    session = fake_session()
    services.add_batch(*batch, repo, session)
    line_not_allocated = ('o2', 'skew', 1)
    
    deallocate_session = fake_session()
    with pytest.raises(LineIsNotAllocatedError):
        services.deallocate(*line_not_allocated, repo, deallocate_session)


def test_add_batch(fake_repository, fake_session):
    repo = fake_repository([])
    session = fake_session()
    services.add_batch('batch', 'skew', 10, None, repo, session)
    assert repo.get('batch').reference == 'batch'


def test_add_batch_commits_on_happy_path(fake_repository, fake_session):
    repo = fake_repository([])
    session = fake_session()
    services.add_batch('batch', 'skew', 10, None, repo, session)
    assert session.commited
