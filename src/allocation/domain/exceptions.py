class DomainException(Exception):
    """Domain-related exceptions."""


class CannotOverallocateError(DomainException):
    """Error raised when trying to allocate an order line with a quantity
    greater than the available quantity in the batch."""


class SKUsDontMatchError(DomainException):
    """Error raised when trying to allocate an order line to a batch with
    mismatching SKUs."""


class LineIsNotAllocatedError(DomainException):
    """Error raised when trying to deallocate an order line that has not been
    allocated previously."""
    def __init__(self, message='This line is not allocated to any batches.'):
        self.message = message
        super().__init__(self.message)


class OrderHasNoAllocations(DomainException):
    """Error raised when trying to query allocations for a order, but the order
    has no allocations."""
    def __init__(self, message='This order has no allocations.'):
        self.message = message
        super().__init__(self.message)


class OutOfStock(DomainException):
    """Error raised when trying to allocate an order line, but there is not
    available quantity either in stock or in shipments."""
    def __init__(self, message='Out of stock for this SKU.'):
        self.message = message
        super().__init__(self.message)


class InvalidSKU(DomainException):
    """Error raised when trying to allocate an OrderLine which SKU is not found
    in any of the batches."""


class BatchDoesNotExist(DomainException):
    """Error raised when trying to get a batch by ref, but there is none"
    by that ref."""
    def __init__(self, message='This batch does not exist.'):
        self.message = message
        super().__init__(self.message)


class InexistentProduct(DomainException):
    """Error raised when trying to use a Product aggregate that does not exist."""
    def __init__(self, message='This SKU does not exist.'):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """Error raised when trying to set an invalid attribute to a command."""


class InvalidTypeForQuantity(ValidationError):
    """Error raised when trying to set a non-integer value to a quantity attribute."""
    def __init__(self, message='Quantity value must be an integer.'):
        self.message = message
        super().__init__(self.message)


class InvalidQuantity(ValidationError):
    """Error raised when trying to set an invalid quantity."""
    def __init__(self, message='Quantity value must be > 1.'):
        self.message = message
        super().__init__(self.message)


class PastETANotAllowed(ValidationError):
    """Error raised when trying to set an ETA that is in the past."""
    def __init__(self, message='Setting an ETA to a past date is not allowed.'):
        self.message = message
        super().__init__(self.message)


class InvalidETAFormat(ValidationError):
    """Error raised when trying to set an ETA with invalid format."""
    def __init__(self, message='ETA must follow the ISO 8601 format'):
        self.message = message
        super().__init__(self.message)
