from dataclasses import dataclass
from datetime import date
from allocation.domain.exceptions import (
    InvalidETAFormat, InvalidQuantity, PastETANotAllowed, InvalidTypeForQuantity
)


@dataclass(frozen=True)
class ValidQtyMixin:
    def __post_init__(self):
        if not isinstance(self.qty, int):
            raise InvalidTypeForQuantity()
        
        if self.qty < 1:
            raise InvalidQuantity()


@dataclass(frozen=True)
class ValidQtyAndETAMixin(ValidQtyMixin):
    def __post_init__(self):
        super().__post_init__()

        if self.eta is None:
            return
        
        if not isinstance(self.eta, date):
            try:
                eta = date.fromisoformat(self.eta)
            except (ValueError, TypeError):
                raise InvalidETAFormat()
        else:
            eta = self.eta
        
        if eta <= date.today():
            raise PastETANotAllowed()
