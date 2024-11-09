from ninja import NinjaAPI
from allocation.adapters.repository import DjangoRepository
from allocation.domain.exceptions import InvalidSKU, LineIsNotAllocatedError, OutOfStock
from allocation.orchestration import services
from allocation.orchestration.uow import DjangoUoW
from dddjango.alloc.schemas import BatchIn, BatchOut, BatchRef, Message, OrderLineIn


api = NinjaAPI()
uow = DjangoUoW()
repo = None
with uow:
    repo = uow.batches


class FakeSession:
    def __init__(self) -> None:
        self._commited = False

    
    @property
    def commited(self):
        return self._commited
    
    
    def commit(self):
        self._commited = True


def get_session():
    return FakeSession()


@api.get('batches/{batch_ref}', response=BatchOut)
def get_batch_by_ref(request, batch_ref: str):
    return 200, repo.get(batch_ref)


@api.post('allocate', response = {201: BatchRef, 400: Message})
def allocate(request, payload: OrderLineIn):
    line = payload.dict()
    session = get_session()
    try:
        batch_ref = services.allocate(
            line['order_id'], line['sku'], line['qty'], repo, session
        )
    except OutOfStock:
        return 400, {'message': 'OutOfStock'}
    except InvalidSKU:
        return 400, {'message': 'InvalidSKU'}
        
    return 201, {'batch_reference': batch_ref}


@api.post('deallocate', response = {200: BatchRef, 400: Message})
def deallocate(request, payload: OrderLineIn):
    line = payload.dict()
    try:
        batch_ref = services.deallocate(
            line['order_id'], line['sku'], line['qty'], uow
        )
    except InvalidSKU:
        return 400, {'message': 'InvalidSKU'}
    except LineIsNotAllocatedError:
        return 400, {'message': 'LineIsNotAllocatedError'}
        
    return 200, {'batch_reference': batch_ref}


@api.post('batches', response={201: BatchOut})
def add_batch(request, payload: BatchIn):
    batch = payload.dict()
    services.add_batch(*batch.values(), uow)
    added_batch = repo.get(batch['reference'])

    return 201, added_batch
