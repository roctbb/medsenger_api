# Medsenger.AI API

## Records by originating contract (0.1.107)

```python
# Existing calls keep returning the patient's history across contracts.
history = api.get_records(contract_id=123, category_name="pulse")

# Only records created under contract 123; historical NULL records are excluded.
records = api.get_records(contract_id=123, category_name="pulse", record_contract_id=123)
count = api.get_records(contract_id=123, category_name="pulse", record_contract_id=123, return_count=True)
categories = api.get_available_categories(contract_id=123, record_contract_id=123)

answers = api.get_multiple_records([
    dict(contract_id=123, category_name="pulse", record_contract_id=123),
    dict(contract_id=123, category_name="weight", record_contract_id=123),
])

# For agents with global patient access:
records = api.get_records(user_id=456, record_contract_id=123)
```

`contract_id` continues to select the patient's access context. The optional
`record_contract_id` filters records by their originating contract and works with
both REST and gRPC, including REST fallback, grouped reads, counts, and batch queries.
The selected contract must belong to the same patient and be accessible to the agent.
Omitting the filter (or passing `None`) preserves the previous behavior.

Returned records include `contract_id` as an integer or `None`. Older records and
user-level Health imports have no originating contract. Existing `add_record` and
`add_records` calls already send the contract; the updated server persists it for
every new record, including batched writes. No changes to writer agents are needed.

Deploy the database migration and **all** REST/gRPC servers before enabling the
filter in clients. Old servers silently ignore the new field. Old clients continue
to work with the new servers; updating the SDK is only necessary to use the new filter
or receive the new field through gRPC. The new parameters are appended to existing
signatures and existing positional arguments remain valid.

## Compliance events

```python
event = api.create_compliance_event(
    contract_id=contract_id,
    external_id="forms-action-request:42",
    code="form_7",
)

api.complete_compliance_event(
    contract_id,
    event_id=event["event"]["id"],
)

# An event can also be addressed by the agent's stable external identifier.
api.cancel_compliance_event(
    contract_id,
    external_id="forms-action-request:42",
)

history = api.get_compliance_events(
    "2026-08-01",
    "2026-08-17",
    user_id=user_id,
    limit=100,
)
```

Exactly one of `event_id` or `external_id` is required when completing or
cancelling an event. History queries similarly require exactly one of
`contract_id` or `user_id`.
