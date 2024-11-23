from allocation.domain import events, queries
from allocation.domain.ports import AbstractQueryRepository


def add_batch(
    batch: events.BatchCreated,
    query_repository: AbstractQueryRepository
):
    query_repository.add_batch(batch.ref, batch.sku, batch.qty, batch.eta)


def add_allocation(
    line: events.LineAllocated,
    query_repository: AbstractQueryRepository
):
    query_repository.add_allocation_for_line(line.order_id, line.sku, line.batch_ref)


def add_order_allocation(
    line: events.LineAllocated,
    query_repository: AbstractQueryRepository
):
    query_repository.add_allocation_for_order(line.order_id, line.sku, line.batch_ref)


def remove_allocation(
    line: events.LineDeallocated,
    query_repository: AbstractQueryRepository
):
    query_repository.remove_allocation_for_line(line.order_id, line.sku)


def remove_allocations_for_order(
    line: events.LineDeallocated,
    query_repository: AbstractQueryRepository
):
    query_repository.remove_allocation_for_order(line.order_id, line.sku)


def update_batch_quantity(
    batch: events.BatchQuantityChanged,
    query_repository: AbstractQueryRepository
):
    query_repository.update_batch_quantity(batch.ref, batch.qty)


def get_batch(
        query: queries.BatchByRef,
        query_repository: AbstractQueryRepository
):
    return query_repository.get_batch(query.batch_ref)


def get_allocation_for_line(
        query: queries.AllocationForLine,
        query_repository: AbstractQueryRepository
):
    return query_repository.get_allocation_for_line(query.order_id, query.sku)


def get_allocations_for_order(
        query: queries.AllocationsForOrder,
        query_repository: AbstractQueryRepository
):
    return query_repository.get_allocations_for_order(query.order_id)
