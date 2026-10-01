"""Explicit Elasticsearch index settings and mappings for `orders`.

The mapping is deliberate rather than dynamic:

* `customer.name` / `customer.email` / `items.title` are `text` (full-text
  search) with a `.keyword` sub-field (aggregations, exact matching).
* `status` is `keyword` so terms filters and facet counts are exact.
* `items` is `nested`, so item level queries stay scoped to a single line.
* monetary values are `double` — Elasticsearch only holds an analytics
  copy of the data; PostgreSQL keeps the precise `NUMERIC(12,2)` values.
"""

from __future__ import annotations

ORDER_INDEX_SETTINGS: dict = {
    "number_of_shards": 1,
    # Single node demo cluster: no replica means instant green status.
    "number_of_replicas": 0,
}

ORDER_INDEX_MAPPING: dict = {
    # Reject anything that is not described below: no accidental schema drift.
    "dynamic": "strict",
    "properties": {
        "order_id": {"type": "long"},
        "order_number": {"type": "keyword"},
        "status": {"type": "keyword"},
        "order_date": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
        "updated_at": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
        "total_amount": {"type": "double"},
        "customer": {
            "type": "object",
            "properties": {
                "id": {"type": "long"},
                "name": {
                    "type": "search_as_you_type",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "email": {
                    "type": "search_as_you_type",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
            },
        },
        "items": {
            "type": "nested",
            "properties": {
                "product_id": {"type": "keyword"},
                "title": {
                    "type": "search_as_you_type",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "quantity": {"type": "integer"},
                "unit_price": {"type": "double"},
                "line_total": {"type": "double"},
            },
        },
    },
}
