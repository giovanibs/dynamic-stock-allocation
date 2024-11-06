from src.dddjango.allocation import models as django_models
import pytest


@pytest.mark.django_db
def test_can_integrate_django():
    django_models.Batch.objects.create(
        reference='django-batch',
        sku='skew',
        purchased_qty=10,
        eta=None
    )
