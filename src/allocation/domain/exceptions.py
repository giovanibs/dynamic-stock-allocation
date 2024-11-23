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
    allocated previously.

    Args:
        msg (str, optional): The error message to be displayed. If not provided,
            a default message will be used.
        line_info (Tuple[str, str], optional): A tuple containing the `order_id`
          and `sku`.
            If provided, a detailed error message will be constructed using this
              information.

    Attributes:
        msg (str): The error message to be displayed.
    """
    def __init__(self, msg=None, line_info=None):
        if msg is None and line_info is None:
            self.msg = 'This line is not allocated to any batches.'
        elif line_info is not None:
            order_id, sku = line_info
            self.msg = f"Line with SKU '{sku}' for order '{order_id}'" \
                 " is not allocated to any batches."
        else:
            self.msg = msg
        super().__init__(self.msg)
        
        
class OrderHasNoAllocations(DomainException):
    """Error raised when trying to query allocations for an order, but the order
    has no allocations.

    Args:
        msg (str, optional): The error message to be displayed. If not provided,
            a default message will be used.
        order_id (str, optional): The ID of the order. If provided, a detailed 
            error message will be constructed using this information.

    Attributes:
        msg (str): The error message to be displayed.
    """
    def __init__(self, msg=None, order_id=None):
        if msg is None and order_id is None:
            self.msg = 'This order has no allocations.'
        elif order_id is not None:
            self.msg = f"Order with id '{order_id}' has no allocations."
        else:
            self.msg = msg
        super().__init__(self.msg)


class OutOfStock(DomainException):
    """Error raised when trying to allocate an order line, but there is not
    available quantity either in stock or in shipments.

    Args:
        msg (str, optional): The error message to be displayed. If not provided,
            a default message will be used.
        sku (str, optional): The SKU of the product. If provided, a detailed
            error message will be constructed using this information.

    Attributes:
        msg (str): The error message to be displayed.
    """
    def __init__(self, msg=None, sku=None):
        if msg is None and sku is None:
            self.msg = 'Out of stock for this SKU.'
        elif sku is not None:
            self.msg = f"Out of stock for SKU '{sku}'."
        else:
            self.msg = msg
        
        super().__init__(self.msg)


class InvalidSKU(DomainException):
    """Error raised when trying to allocate an OrderLine which SKU is not found
    in any of the batches."""


class BatchDoesNotExist(DomainException):
    """Error raised when trying to get a batch by ref, but there is none by that ref.

    Args:
        msg (str, optional): The error message to be displayed. If not provided,
            a default message will be used.
        ref (str, optional): The reference of the batch. If provided, a detailed
            error message will be constructed using this information.

    Attributes:
        msg (str): The error message to be displayed.
    """
    def __init__(self, msg=None, ref=None):
        if msg is None and ref is None:
            self.msg = 'This batch does not exist.'
        elif ref is not None:
            self.msg = f"Batch with reference '{ref}' does not exist."
        else:
            self.msg = msg
        super().__init__(self.msg)


class InexistentProduct(DomainException):
    """Error raised when trying to use a Product aggregate that does not exist.

    Args:
        msg (str, optional): The error message to be displayed. If not provided,
            a default message will be used.
        sku (str, optional): The SKU of the product. If provided, a detailed
            error message will be constructed using this information.

    Attributes:
        msg (str): The error message to be displayed.
    """
    def __init__(self, msg=None, sku=None):
        if msg is None and sku is None:
            self.msg = 'This SKU does not exist.'
        elif sku is not None:
            self.msg = f"SKU '{sku}' does not exist."
        else:
            self.msg = msg
        super().__init__(self.msg)
            

class ValidationError(Exception):
    """Error raised when trying to set an invalid attribute to a command."""


class InvalidTypeForQuantity(ValidationError):
    """Error raised when trying to set a non-integer value to a quantity attribute."""
    def __init__(self, msg='Quantity value must be an integer.'):
        self.msg = msg
        super().__init__(self.msg)


class InvalidQuantity(ValidationError):
    """Error raised when trying to set an invalid quantity."""
    def __init__(self, msg='Quantity value must be > 1.'):
        self.msg = msg
        super().__init__(self.msg)


class PastETANotAllowed(ValidationError):
    """Error raised when trying to set an ETA that is in the past."""
    def __init__(self, msg='Setting an ETA to a past date is not allowed.'):
        self.msg = msg
        super().__init__(self.msg)


class InvalidETAFormat(ValidationError):
    """Error raised when trying to set an ETA with invalid format."""
    def __init__(self, msg='ETA must follow the ISO 8601 format'):
        self.msg = msg
        super().__init__(self.msg)
