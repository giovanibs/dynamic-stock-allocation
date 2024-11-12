# Definitions and rules for stock allocation

## `product`

The smalles unit in the system.

- `product`
  - `sku`: (stock-keeping-unit) `product`'s unique identifier.

## `order`

Costumers place an `order` in the ecommerce system.

- `order`
  - `order ref`: `order`'s unique identifier.
  - `order line`s: products being purchased by the customer and their respective quantity.
    - `sku`
    - `quantity`

## `batch`

Batches of stock may exist in the `warehouse stock`, or `in transit` if they are shipping after being ordered by the purchasing department, in which case they will have an `ETA`.

- `batch`
  - `ref`: batch's unique identifier
  - `sku`
  - `quantity`
  - `eta`: estimated time of arrival if the batch is shipping
  - `in warehouse stock`

## Allocation logic

- `Order lines` are allocated to `batches`
  - allocating a given `quantity` of a `product` to the `batch` will decrease the `batch`'s `available quantity` by that same amount
  - cannot allocate `order lines` to a `batch` if it doesn't have the required `quantity` available
  - the same `order line` cannot be allocated more than once in the same `batch`
  - batches in `warehouse stock` takes pref over shipping batches
  - shipping batches with the earliest `eta` takes pref when allocating to them
  