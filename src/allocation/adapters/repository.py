from abc import ABC, abstractmethod
import src.allocation.domain.model as model


class AbstractRepository(ABC):

    @abstractmethod
    def add(self, batch: model.Batch) -> None:
        raise NotImplementedError()


    @abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError()
