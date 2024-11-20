from allocation.domain import events
from allocation.orchestration.uow import AbstractUnitOfWork


def add_batch(batch: events.BatchCreated, uow: AbstractUnitOfWork):
    uow.querier.add_batch(batch.ref, batch.sku, batch.qty, batch.eta)


def add_allocation(line: events.LineAllocated, uow: AbstractUnitOfWork):
    uow.querier.add_allocation_for_line(line.order_id, line.sku, line.batch_ref)


def add_order_allocation(line: events.LineAllocated, uow: AbstractUnitOfWork):
    uow.querier.add_allocation_for_order(line.order_id, line.sku, line.batch_ref)


def remove_allocation(line: events.LineDeallocated, uow: AbstractUnitOfWork):
    uow.querier.remove_allocation_for_line(line.order_id, line.sku)


def remove_allocations_for_order(line: events.LineDeallocated, uow: AbstractUnitOfWork):
    uow.querier.remove_allocation_for_order(line.order_id, line.sku)


def update_batch_quantity(batch: events.BatchQuantityChanged, uow: AbstractUnitOfWork):
    uow.querier.update_batch_quantity(batch.ref, batch.qty)
