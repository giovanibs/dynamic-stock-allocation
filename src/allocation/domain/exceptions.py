"""Domain exceptions to be used in the project."""

class CannotOverallocateError(Exception):
    """Error raised when trying to allocate an order line with a quantity
    greater than the available quantity in the batch."""


class SKUsDontMatchError(Exception):
    """Error raised when trying to allocate an order line to a batch with
    mismatching SKUs."""


class LineIsNotAllocatedError(Exception):
    """Error raised when trying to deallocate an order line that has not been
    allocated previously."""


class OutOfStock(Exception):
    """Error raised when trying to allocate an order line, but there is not
    available quantity either in stock or in shipments."""