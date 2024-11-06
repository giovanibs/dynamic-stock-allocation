from abc import ABC, abstractmethod
import src.allocation.domain.model as model
from src.dddjango.allocation import models as django_models


class AbstractRepository(ABC):

    @abstractmethod
    def add(self, batch: model.Batch) -> None:
        raise NotImplementedError()


    @abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError()
    

class DjangoRepository(AbstractRepository):

    def add(self, batch: model.Batch) -> None:
        django_models.Batch.objects.create(**batch.properties_dict)

    
    def get(self, reference) -> model.Batch:
        return django_models.Batch.objects.get(reference=reference).to_domain()
