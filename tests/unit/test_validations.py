from datetime import date, timedelta
import pytest

from allocation.domain import commands
from allocation.domain.exceptions import (
    InvalidETAFormat, InvalidQuantity, InvalidTypeForQuantity, PastETANotAllowed
)


@pytest.mark.parametrize(
    (   'command', 'qty_value', 'expected_error'),
    [
        (commands.CreateBatch, 'a', InvalidTypeForQuantity),
        (commands.Allocate   , 'a', InvalidTypeForQuantity),
        (commands.Deallocate , 'a', InvalidTypeForQuantity),
        (commands.Reallocate , 'a', InvalidTypeForQuantity),
       
        (commands.CreateBatch, 0, InvalidQuantity),
        (commands.Allocate   , 0, InvalidQuantity),
        (commands.Deallocate , 0, InvalidQuantity),
        (commands.Reallocate , 0, InvalidQuantity),

        (commands.CreateBatch, -1, InvalidQuantity),
        (commands.Allocate   , -1, InvalidQuantity),
        (commands.Deallocate , -1, InvalidQuantity),
        (commands.Reallocate , -1, InvalidQuantity),
    ]
)
def test_cannot_set_invalid_quantity(command, qty_value, expected_error):
    with pytest.raises(expected_error):
        command('foo', 'bar', qty_value)


@pytest.mark.parametrize(
    ('qty_value', 'expected_error'),
    [
        ('a', InvalidTypeForQuantity),
        (0, InvalidQuantity),
        (-1, InvalidQuantity),
    ]
)
def test_cannot_change_batch_qty_to_invalid_value(qty_value, expected_error):
    with pytest.raises(expected_error):
        commands.ChangeBatchQuantity('foo', qty_value)


@pytest.mark.parametrize(
    ('eta_value', 'expected_error'),
    [
        ('aaaaaa', InvalidETAFormat),
        (20240101, InvalidETAFormat),
        ('202401', InvalidETAFormat),
        ('2024.01.01', InvalidETAFormat),
        ('2024/01/01', InvalidETAFormat),

        (date.today() - timedelta(days=1), PastETANotAllowed),
        ((date.today() - timedelta(days=1)).isoformat(), PastETANotAllowed),
    ]
)
def test_cannot_set_invalid_eta(eta_value, expected_error):
    with pytest.raises(expected_error):
        commands.CreateBatch('foo', 'bar', 1, eta_value)
