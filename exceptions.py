"""Exceptions/errors to be used in the project."""

class CannotOverallocateError(Exception):
    """Error raised when trying to allocate an order line with a quantity
    greater than the available quantity in the batch."""


class SKUsDontMatchError(Exception):
    """Error raised when trying to allocate an order line to a batch with
    mismatching SKUs."""