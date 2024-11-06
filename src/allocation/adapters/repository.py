from abc import ABC, abstractmethod
from allocation.domain import model as domain_models
from dddjango.allocation import models as django_models


class AbstractRepository(ABC):

    @abstractmethod
    def add(self, batch: domain_models.Batch) -> None:
        raise NotImplementedError()


    @abstractmethod
    def get(self, reference) -> domain_models.Batch:
        raise NotImplementedError()
    

class DjangoRepository(AbstractRepository):

    def add(self, batch: domain_models.Batch) -> None:
        
        django_batch = django_models.Batch(**batch.properties_dict)
        django_batch.save()
        for line in batch._allocations:
            django_models.Allocation.objects.create(
                batch=django_batch, order_id=line.order_id, sku=line.sku, qty=line.qty
            )
    
    def get(self, reference) -> domain_models.Batch:
        return django_models.Batch.objects.get(reference=reference).to_domain()
