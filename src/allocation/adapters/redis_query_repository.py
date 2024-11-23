from datetime import date
from typing import Optional
import redis
from allocation.domain.ports import AbstractQueryRepository
from allocation.domain import exceptions, model as domain_
import pickle


class RedisQueryRepository(AbstractQueryRepository):
    
    def __init__(self, redis_host, redis_port) -> None:
        self._client: redis.Redis = redis.Redis(redis_host, redis_port)
    
    
    def add_batch(self, ref: str, sku: str, qty: int, eta: Optional[date] = None):
        serialized_batch = pickle.dumps(domain_.Batch(ref, sku, qty, eta))
        self._client.hset('batches', ref, serialized_batch)


    def get_batch(self, ref: str):
        batch_data = self._client.hget('batches', ref)
        
        if batch_data is None:
            raise exceptions.BatchDoesNotExist()
        
        return pickle.loads(batch_data)


    def update_batch_quantity(self, ref: str, qty: int):
        domain_batch = self.get_batch(ref)
        batch_dict = domain_batch.properties_dict
        batch_dict['qty'] = qty
        self.add_batch(**batch_dict)


    def add_allocation_for_line(self, order_id, sku, batch_ref):
        self._client.hset('allocation', f'{order_id}--{sku}', batch_ref)


    def get_allocation_for_line(self, order_id: str, sku: str) -> str:
        batch_ref = self._client.hget('allocation', f'{order_id}--{sku}')

        if batch_ref is None:
            raise exceptions.LineIsNotAllocatedError()
        
        return batch_ref


    def remove_allocation_for_line(self, order_id, sku):
        self._client.hdel('allocation', f'{order_id}--{sku}')


    def add_allocation_for_order(self, order_id, sku, batch_ref):
        new_allocation = {sku: batch_ref}
        
        try:
            allocations = self.get_allocations_for_order(order_id)
            allocations.append(new_allocation)
        except exceptions.OrderHasNoAllocations:
            allocations = [new_allocation]
        
        self._client.hset('order_allocations', order_id, pickle.dumps(allocations))


    def get_allocations_for_order(self, order_id: str):
        allocations = self._client.hget('order_allocations', order_id)

        if allocations is None:
            raise exceptions.OrderHasNoAllocations()
        
        return pickle.loads(allocations)


    def remove_allocation_for_order(self, order_id, sku):
        allocations = self.get_allocations_for_order(order_id)
        allocations = [a for a in allocations if sku not in a]
        self._client.hset('order_allocations', order_id, pickle.dumps(allocations))
