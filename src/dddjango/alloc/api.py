from typing import List, Optional, Union
from ninja import Field, NinjaAPI
from ninja.schema import Schema
from allocation.adapters.repository import DjangoRepository
from datetime import date


class BatchOut(Schema):
    reference: str
    sku: str
    allocated_qty: int
    available_qty: int
    eta: Union[date, None]


api = NinjaAPI()
repo = DjangoRepository()


@api.get('/{batch_ref}', response=BatchOut)
def get_batch_by_ref(request, batch_ref: str):
    return repo.get(batch_ref)
