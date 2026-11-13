import logging
import json
import time
import zlib
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def utcnow():
    # The existing agent schema stores naive UTC timestamps.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_table(metadata):
    if 'agent_cache_updates' in metadata.tables:
        return metadata.tables['agent_cache_updates']
    table = sa.Table(
        'agent_cache_updates',
        metadata,
        sa.Column('agent_key', sa.String(64), primary_key=True),
        sa.Column('contract_id', sa.Integer, primary_key=True),
        sa.Column('requested', sa.BigInteger, nullable=False),
        sa.Column('delivered', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('due_at', sa.DateTime, nullable=False),
        sa.Column('attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_error', sa.String(128)),
    )
    sa.Index(
        'ix_agent_cache_updates_pending',
        table.c.agent_key,
        table.c.due_at,
        postgresql_where=table.c.requested > table.c.delivered,
        sqlite_where=table.c.requested > table.c.delivered,
    )
    return table


class CacheUpdateOutbox:
    """One pending row per agent/contract, committed with the changed objects.

    Projections return (contract_id, cache_relevant_value), or None. They must be
    pure: no SQL, HTTP, timestamps, tokens or mutation of model JSON. SQLAlchemy
    flushes AND ORM bulk updates/deletes are covered. Raw SQL must use record().
    """

    def __init__(
        self,
        metadata,
        engine,
        agent_key,
        send,
        active,
        enabled=lambda: True,
        window=0.5,
    ):
        self.table = create_table(metadata)
        self.engine = engine
        self.agent_key = agent_key
        self.send = send
        self.active = active
        self.enabled = enabled
        self.window = window
        self.projections = {}
        self._batch = ContextVar('cache_batch_' + agent_key, default=None)
        # Several Flask apps/adapters may coexist in one process (e.g. tests).
        self._pending_key = object()
        self._scope = zlib.crc32(('agent-cache:' + agent_key).encode()) & 0x7FFFFFFF

    def watch(self, model, projection):
        self.projections[model] = projection

    def install(self):
        sa.event.listen(Session, 'before_flush', self._before_flush)
        sa.event.listen(Session, 'after_flush_postexec', self._after_flush)
        sa.event.listen(Session, 'after_soft_rollback', self._rollback)
        sa.event.listen(Session, 'do_orm_execute', self._bulk)

    def uninstall(self):
        for name, callback in [
            ('before_flush', self._before_flush),
            ('after_flush_postexec', self._after_flush),
            ('after_soft_rollback', self._rollback),
            ('do_orm_execute', self._bulk),
        ]:
            sa.event.remove(Session, name, callback)

    @contextmanager
    def batch(self):
        """Group intermediate commits; process death releases the PostgreSQL lock.

        The durable row is never held only in memory. On failure, already committed
        changes remain pending; rolled-back changes do not create an invalidation.
        """
        if self._batch.get() is not None or not self.enabled():
            yield
            return
        connections = {}
        token = self._batch.set(connections)
        try:
            yield
        finally:
            self._batch.reset(token)
            for connection, ids in connections.values():
                try:
                    for cid in ids:
                        connection.execute(
                            sa.text('SELECT pg_advisory_unlock_shared(:scope, :id)'),
                            {'scope': self._scope, 'id': cid},
                        )
                    connection.commit()
                except Exception:
                    # Session advisory locks must never return to the pool.
                    connection.invalidate()
                    raise
                finally:
                    connection.close()

    def _hold(self, connection, cid):
        if connection.dialect.name != 'postgresql':
            return  # SQLite is useful for transaction tests; production uses PostgreSQL.
        batch = self._batch.get()
        if batch is None:
            connection.execute(
                sa.text('SELECT pg_advisory_xact_lock_shared(:scope, :id)'),
                {'scope': self._scope, 'id': cid},
            )
            return
        engine = connection.engine
        if engine not in batch:
            batch[engine] = (engine.connect(), set())
        held, ids = batch[engine]
        if cid not in ids:
            held.execute(
                sa.text('SELECT pg_advisory_lock_shared(:scope, :id)'),
                {'scope': self._scope, 'id': cid},
            )
            held.commit()
            ids.add(cid)

    def _project(self, model, row):
        return self.projections[model](dict(row)) if row is not None else None

    @staticmethod
    def _same(before, after):
        # Python considers False == 0 == 0.0. These are distinct API values.
        return json.dumps(before, sort_keys=True, allow_nan=False) == json.dumps(
            after, sort_keys=True, allow_nan=False
        )

    def _before_flush(self, session, *_):
        if not self.enabled():
            return
        pending = []
        for obj in set(session.new) | set(session.dirty) | set(session.deleted):
            model = type(obj)
            if model not in self.projections:
                continue
            table = model.__table__
            connection = session.connection(bind_arguments={'mapper': model})
            identity = sa.inspect(obj).identity
            old = (
                connection.execute(sa.select(table).where(table.c.id == identity[0]))
                .mappings()
                .first()
                if identity
                else None
            )
            before = self._project(model, old)
            after = (
                self._project(
                    model, {c.name: getattr(obj, c.name) for c in table.columns}
                )
                if obj not in session.deleted
                else None
            )
            if identity and self._same(before, after):
                continue
            # Acquire before writing, including changes whose generated ID will
            # only become available after flush.
            ids = {view[0] for view in (before, after) if view}
            for cid in sorted(ids):
                self._hold(connection, cid)
            pending.append((obj, before, obj in session.deleted))
        session.info[self._pending_key] = pending

    def _after_flush(self, session, *_):
        changed = set()
        for obj, before, deleted in session.info.pop(self._pending_key, []):
            after = (
                None
                if deleted
                else self._project(
                    type(obj),
                    {c.name: getattr(obj, c.name) for c in obj.__table__.columns},
                )
            )
            if not self._same(before, after):
                changed.update(view[0] for view in (before, after) if view)
        for cid in sorted(changed):
            self.record(session.connection(), cid)

    def _rollback(self, session, *_):
        session.info.pop(self._pending_key, None)

    def _bulk(self, state):
        model = state.bind_mapper.class_ if state.bind_mapper else None
        if (
            not self.enabled()
            or model not in self.projections
            or not (state.is_update or state.is_delete)
        ):
            return
        if isinstance(state.parameters, list):
            raise ValueError(
                'Use ORM objects or explicit cache invalidation for tracked executemany updates'
            )
        table = model.__table__
        connection = state.session.connection(bind_arguments={'mapper': model})
        query = sa.select(table)
        if state.statement.whereclause is not None:
            query = query.where(state.statement.whereclause)
        rows = connection.execute(query, state.parameters or {}).mappings().all()
        before = {row['id']: self._project(model, row) for row in rows}
        for cid in sorted({v[0] for v in before.values() if v}):
            self._hold(connection, cid)
        result = state.invoke_statement()
        rows = (
            connection.execute(sa.select(table).where(table.c.id.in_(before)))
            .mappings()
            .all()
            if state.is_update
            else []
        )
        after = {row['id']: self._project(model, row) for row in rows}
        changed = set()
        for key in before.keys() | after.keys():
            if not self._same(before.get(key), after.get(key)):
                changed.update(v[0] for v in (before.get(key), after.get(key)) if v)
        for cid in sorted(changed):
            self.record(connection, cid)
        return result

    def record(self, connection, contract_id):
        """Call inside the SAME transaction as an explicit/raw SQL mutation."""
        if not self.enabled():
            return
        self._hold(connection, contract_id)
        if connection.dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import insert
        elif connection.dialect.name == 'sqlite':
            from sqlalchemy.dialects.sqlite import insert
        else:
            raise RuntimeError('Cache outbox requires PostgreSQL')
        t = self.table
        due = utcnow() + timedelta(seconds=self.window)
        statement = insert(t).values(
            agent_key=self.agent_key,
            contract_id=contract_id,
            requested=1,
            delivered=0,
            due_at=due,
            attempts=0,
        )
        connection.execute(
            statement.on_conflict_do_update(
                index_elements=[t.c.agent_key, t.c.contract_id],
                set_={
                    'requested': t.c.requested + 1,
                    # A fixed window cannot be postponed forever by continuous activity.
                    'due_at': sa.case(
                        (t.c.requested == t.c.delivered, due), else_=t.c.due_at
                    ),
                },
            )
        )

    def drain(self, limit=100):
        if not self.enabled():
            return 0
        t = self.table
        with self.engine().connect() as connection:
            ids = (
                connection.execute(
                    sa.select(t.c.contract_id)
                    .where(
                        t.c.agent_key == self.agent_key,
                        t.c.requested > t.c.delivered,
                        t.c.due_at <= utcnow(),
                    )
                    .order_by(t.c.due_at)
                    .limit(limit)
                )
                .scalars()
                .all()
            )
        return sum(self.deliver(cid) for cid in ids)

    def deliver(self, contract_id):
        t = self.table
        key = sa.and_(t.c.agent_key == self.agent_key, t.c.contract_id == contract_id)
        with self.engine().connect() as connection:
            postgres = connection.dialect.name == 'postgresql'
            acquired = (
                not postgres
                or connection.execute(
                    sa.text('SELECT pg_try_advisory_lock(:scope, :id)'),
                    {'scope': self._scope, 'id': contract_id},
                ).scalar()
            )
            connection.commit()
            if not acquired:
                return 0
            try:
                row = connection.execute(sa.select(t).where(key)).mappings().first()
                if (
                    not row
                    or row['requested'] <= row['delivered']
                    or row['due_at'] > utcnow()
                ):
                    return 0
                active = self.active(connection, contract_id)
                connection.commit()  # Never keep a DB transaction open across HTTP.
                try:
                    if active and self.send(contract_id) != 'ok':
                        raise RuntimeError('Cache refresh was not acknowledged')
                except Exception as error:
                    connection.execute(
                        t.update()
                        .where(key)
                        .values(
                            attempts=row['attempts'] + 1,
                            due_at=utcnow()
                            + timedelta(seconds=min(60, 2 ** min(row['attempts'], 6))),
                            last_error=type(error).__name__[:128],
                        )
                    )
                    connection.commit()
                    logger.warning(
                        'Cache refresh deferred: agent=%s contract=%s error=%s',
                        self.agent_key,
                        contract_id,
                        type(error).__name__,
                    )
                    return 0
                connection.execute(
                    t.update()
                    .where(key)
                    .values(delivered=row['requested'], attempts=0, last_error=None)
                )
                connection.commit()
                return 1
            finally:
                try:
                    connection.rollback()
                    if postgres:
                        connection.execute(
                            sa.text('SELECT pg_advisory_unlock(:scope, :id)'),
                            {'scope': self._scope, 'id': contract_id},
                        )
                        connection.commit()
                except Exception:
                    connection.invalidate()
                    raise

    def install_flask(self, app):
        from flask import g

        name = '_cache_batch_' + self.agent_key

        @app.before_request
        def begin_cache_batch():
            context = self.batch()
            context.__enter__()
            setattr(g, name, context)

        @app.teardown_request
        def finish_cache_batch(error):
            context = g.pop(name, None)
            if context:
                context.__exit__(None, None, None)

    def run_worker(self, app):
        while True:
            try:
                with app.app_context():
                    self.drain()
            except Exception:
                logger.exception('Cache outbox poll failed: agent=%s', self.agent_key)
            time.sleep(0.5)
