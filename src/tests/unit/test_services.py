import pytest
from allocation.domain.exceptions import (
    InvalidSKU, LineIsNotAllocatedError, OutOfStock)
from allocation.orchestration import services


@pytest.fixture
def batch(tomorrow):
    return ('batch', 'skew', 10, tomorrow)


def test_allocate_commits_on_happy_path(batch, repo, fake_session):
    services.add_batch(*batch, repo, fake_session())
    line = ('o1', 'skew', 1)
    
    session = fake_session()
    services.allocate(*line, repo, session)
    assert session.commited == True


def test_allocate_does_not_commit_on_error(batch, repo, fake_session):
    services.add_batch(*batch, repo, fake_session())
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    line_with_greater_qty = ('o2', 'skew', 11)
    
    session = fake_session()
    try:
        services.allocate(*line_with_invalid_sku, repo, session)
    except InvalidSKU:
        pass
    
    assert session.commited == False

    try:
        services.allocate(*line_with_greater_qty, repo, session)
    except OutOfStock:
        pass

    assert session.commited == False


def test_allocate_returns_batch_reference(today, later, repo, fake_session):
    earlier_batch = ('earlier', 'skew', 10, today)
    later_batch = ('earlier', 'skew', 10, later)
    services.add_batch(*earlier_batch, repo, fake_session())
    services.add_batch(*later_batch, repo, fake_session())
    line = ('o1', 'skew', 1)
    
    session = fake_session()
    batch_reference = services.allocate(*line, repo, session)
    assert batch_reference == earlier_batch[0]


def test_allocate_raises_error_for_invalid_sku(batch, repo, fake_session):
    services.add_batch(*batch, repo, fake_session())
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    session = fake_session()
    with pytest.raises(InvalidSKU):
        services.allocate(*line_with_invalid_sku, repo, session)


def test_allocate_raises_error_for_overallocation(batch, repo, fake_session):
    services.add_batch(*batch, repo, fake_session())
    line_with_greater_qty = ('o2', 'skew', 11)
    
    session = fake_session()
    with pytest.raises(OutOfStock):
        services.allocate(*line_with_greater_qty, repo, session)


def test_deallocate_returns_batch_reference(repo, fake_session):
    batch_with_the_line = ('it_is_me', 'skew', 10, None)
    batch_without_the_line = ('it_is_not_me', 'skew', 1, None)
    services.add_batch(*batch_with_the_line, repo, fake_session())
    services.add_batch(*batch_without_the_line, repo, fake_session())
    line = ('o1', 'skew', 10)
    services.allocate(*line, repo, fake_session())
    
    session = fake_session()
    batch_reference = services.deallocate(*line, repo, session)
    assert batch_reference == batch_with_the_line[0]


def test_deallocate_commits_on_happy_path(batch, repo, fake_session):
    services.add_batch(*batch, repo, fake_session())
    line = ('o1', 'skew', 1)
    services.allocate(*line, repo, fake_session())
    
    session = fake_session()
    services.deallocate(*line, repo, session)
    assert session.commited == True


def test_deallocate_does_not_commit_on_error(batch, repo, fake_session):
    services.add_batch(*batch, repo, fake_session())
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    line_not_allocated = ('o2', 'skew', 1)
    
    session = fake_session()
    try:
        services.deallocate(*line_with_invalid_sku, repo, session)
    except InvalidSKU:
        pass
    
    assert session.commited == False

    try:
        services.deallocate(*line_not_allocated, repo, session)
    except LineIsNotAllocatedError:
        pass

    assert session.commited == False


def test_deallocate_raises_error_for_invalid_sku(batch, repo, fake_session):
    services.add_batch(*batch, repo, fake_session())
    line_with_invalid_sku = ('o1', 'invalid_skew', 1)
    
    session = fake_session()
    with pytest.raises(InvalidSKU):
        services.deallocate(*line_with_invalid_sku, repo, session)


def test_deallocate_raises_error_for_not_allocated_line(batch, repo, fake_session):
    services.add_batch(*batch, repo, fake_session())
    line_not_allocated = ('o2', 'skew', 1)
    
    session = fake_session()
    with pytest.raises(LineIsNotAllocatedError):
        services.deallocate(*line_not_allocated, repo, session)


def test_add_batch(batch, repo, fake_session):
    services.add_batch(*batch, repo, fake_session())
    assert repo.get('batch').reference == batch[0]


def test_add_batch_commits_on_happy_path(batch, repo, fake_session):
    session = fake_session()
    services.add_batch(*batch, repo, session)
    assert session.commited
