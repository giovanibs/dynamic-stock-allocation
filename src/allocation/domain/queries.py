from dataclasses import dataclass


class Query:
    pass


@dataclass(frozen=True)
class BatchByRef(Query):
    batch_ref: str


@dataclass(frozen=True)
class AllocationForLine(Query):
    order_id: str
    sku: str


@dataclass(frozen=True)
class AllocationsForOrder(Query):
    order_id: str
