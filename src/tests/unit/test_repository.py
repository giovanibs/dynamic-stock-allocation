from allocation.domain.model import Batch, OrderLine


def test_can_retrieve_batch(fake_repository):
    batch = Batch('batch', 'sku', 100)
    repo = fake_repository([batch])
    retrieved_batch = repo.get(batch.reference)
    assert_batches_match(retrieved_batch, batch)


def test_can_add_batch(fake_repository):
    batch = Batch('batch', 'sku', 100)
    repo = fake_repository([batch])
    repo.add(batch)
    retrieved_batch = repo.get(batch.reference)
    assert_batches_match(retrieved_batch, batch)


def test_can_update_batch(fake_repository):
    batch = Batch('batch', 'sku', 100)
    repo = fake_repository([batch])
    line1 = OrderLine('o1', 'sku', 10)
    batch.allocate(line1)
    repo.update(batch)
    updated_batch = repo.get(batch.reference)
    assert_batches_match(updated_batch, batch)


def test_can_list_batches(fake_repository):
    batches = [
        Batch('batch1', 'sku', 100),
        Batch('batch2', 'sku', 100),
        Batch('batch3', 'sku', 100),
    ]
    repo = fake_repository(batches)
    retrieved_batches = repo.list()
    assert len(retrieved_batches) == 3

    for batch in batches:
        assert_batches_match(
            batch,
            next(b for b in retrieved_batches if b.reference == batch.reference)
        )


def assert_batches_match(batch: Batch, other_batch: Batch):
    assert batch.reference == other_batch.reference
    assert batch.sku == other_batch.sku
    assert batch.allocated_qty == other_batch.allocated_qty
    assert batch.available_qty == other_batch.available_qty
    assert batch.eta == other_batch.eta
    assert batch._allocations == other_batch._allocations
