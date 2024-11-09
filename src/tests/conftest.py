from typing import List
import pytest
from django.core.management import call_command
from datetime import date, timedelta
from allocation.adapters.repository import AbstractRepository
from allocation.domain.exceptions import BatchDoesNotExist
from allocation.domain.model import Batch, OrderLine
from allocation.orchestration.uow import AbstractUnitOfWork


@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    with django_db_blocker.unblock():
        call_command('migrate', verbosity=0)


@pytest.fixture(scope='session')
def today():
    return date.today()


@pytest.fixture(scope='session')
def tomorrow(today):
    return today + timedelta(days=1)


@pytest.fixture(scope='session')
def later(today):
    return today + timedelta(days=2)


@pytest.fixture(scope='session')
def fake_repository():


    class FakeRepository(AbstractRepository):

        def __init__(self, batches: List[Batch] = None) -> None:
            super().__init__()
            self._batches = set()
            if batches is not None:
                for batch in batches:
                    self.add(batch)

        
        def _get(self, reference: str) -> Batch:
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

    return FakeRepository


@pytest.fixture(scope='session')
def repo(fake_repository):
    return fake_repository()


@pytest.fixture(scope='session')
def fake_session():

    class FakeSession:
        def __init__(self) -> None:
            self._commited = False

        
        @property
        def commited(self):
            return self._commited
        
        
        def commit(self):
            self._commited = True

    return FakeSession


@pytest.fixture(scope='session')
def fake_uow(repo):

    class FakeUow(AbstractUnitOfWork):

        def __init__(self, repo: AbstractRepository) -> None:
            self._batches = repo
            self._commited = False


        @property
        def commited(self) -> bool:
            return self._commited
        

        @property
        def batches(self) -> AbstractRepository:
            return self._batches
        

        def __enter__(self) -> AbstractUnitOfWork:
            self._commited = False
            return super().__enter__()
        

        def __exit__(self, *args) -> None:
            return super().__exit__(*args)


        def commit(self):
            self._commited = True


        def rollback(self):
            pass

    return FakeUow(repo)
