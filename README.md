# Medsenger.AI API

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
