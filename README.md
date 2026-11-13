# Medsenger.AI API

## Doctor contracts, including completed ones

```python
current = api.get_doctor_info(doctor_id=42)
all_contracts = api.get_all_doctor_info(doctor_id=42)
```

`get_all_doctor_info` calls `POST /api/agents/doctor/info/all` with the same
`api_key` and `doctor_id` as `/doctor/info`. Both methods return `state`, `doctor`,
`contracts`, and `doctor_contracts` in the same format. The new method also includes
expired and manually closed contracts; each contract retains its `active` flag.
Both methods include primary and helper doctor assignments and only contracts
currently connected to the agent. If an agent is detached when a contract closes,
that contract is no longer accessible through either method. Reporting agents that
need archived contracts should have `keep_alive_after_close` enabled before closure.
Deploy the updated server before using the new method; no database migration is needed.

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


## Coalesced cache invalidation (0.1.109)

Install `medsenger-api[cache]` (SQLAlchemy 2.x). `CacheUpdateOutbox` is an optional
adapter: it does not change `/api/agents/cache`, `/params`, `/actions` or socket payloads.
A pure projection specifies which persisted fields affect an agent's cache.
Changes to watched models and ORM bulk updates/deletes write one durable pending
row per `(agent_key, contract_id)` in the SAME transaction. Raw SQL and bulk
executemany must explicitly record invalidations; they must not silently bypass tracking.

`batch()` groups a request/task containing intermediate commits. PostgreSQL
shared advisory locks prevent publishing its intermediate state, while an
exclusive publisher lock prevents two workers from publishing the same revision.
The publisher does not hold a database transaction during HTTP. A committed
partial operation remains pending on failure; rolled-back changes disappear.
A process crash releases its locks. HTTP failures retain the row with bounded
retry delays; clinical operations are never retried by this component.

Watch only actual dependencies: forms' visible buttons and editable parameter
values/locations; call booking visibility and visible locale; heart activation and upload-key revision.
Runtime timers and device settings not present in the response do not invalidate.
The renderer and projection should share pure code. Preserve array order and
scalar types; do not include timestamps or freshly issued tokens in projections.
A fresh token inside an actual backend snapshot must still be compared normally.
External dependencies (patient profile, category metadata, token rotation) still
require their existing backend invalidation paths; the agent observer does not
claim to observe another service's database.

Run one standalone `run_worker(app)` process per agent initially. The fixed 0.5 s
coalescing window is not extended by additional changes. Requests/tasks for other
contracts remain independent. Multiple publishers are safe; measure pending age
and throughput before increasing their number. Keep agent Flask workers available
for the backend's `/params` and `/actions` callbacks.

Tests: `TEST_POSTGRES_URL=<isolated-test-database> python -m unittest discover -s tests -p 'test_cache_*.py'`.
The PostgreSQL suite resets its test tables: never use an application database.
